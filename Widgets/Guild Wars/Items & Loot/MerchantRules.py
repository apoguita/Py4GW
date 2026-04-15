import json
import os
import re
import shutil
import time
import traceback
from collections.abc import Callable
from hashlib import md5
from dataclasses import asdict, dataclass, field, replace
from urllib.parse import unquote

import Py4GW
import PyImGui

from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Console
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Map
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Player
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.marks_sources.mods_parser import ModDatabase
from Sources.marks_sources.mods_parser import MatchedRuneInfo
from Sources.marks_sources.mods_parser import MatchedWeaponModInfo
from Sources.marks_sources.mods_parser import parse_modifiers
from Sources.modular_bot.recipes.actions_inventory import DEFAULT_NPC_SELECTORS
from Sources.modular_bot.recipes.actions_inventory import SUPPORTED_MAP_NPC_SELECTORS
from Sources.modular_bot.recipes.step_selectors import resolve_agent_xy_from_step


MODULE_NAME = "Merchant Rules"
MODULE_ICON = "Textures\\Module_Icons\\MerchantRules.png"
FLOATING_UI_INI_PATH = "Widgets/Guild Wars/Items & Loot/MerchantRules"
FLOATING_UI_INI_FILENAME = "MerchantRulesFloating.ini"
FLOATING_ICON_WINDOW_ID = "##merchant_rules_floating_icon_button"
FLOATING_ICON_WINDOW_NAME = "Merchant Rules Toggle"

PROFILE_VERSION = 16
CONFIG_DIR = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "MerchantRules")
SHARED_PROFILES_DIR = os.path.join(CONFIG_DIR, "Profiles")
RECOVERY_DIR = os.path.join(CONFIG_DIR, "Recovery")
DATA_DIR = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Data")
CATALOG_PATH = os.path.join(DATA_DIR, "merchant_rules_catalog.json")
ITEMS_CATALOG_PATH = os.path.join(DATA_DIR, "merchant_rules_items_catalog.json")
DROP_DATA_PATH = os.path.join(DATA_DIR, "modelid_drop_data.json")
ITEM_HANDLING_ITEMS_CATALOG_PATH = os.path.join(
    Py4GW.Console.get_projects_path(),
    "Sources",
    "frenkeyLib",
    "ItemHandling",
    "Items",
    "items.json",
)
MODS_DATA_DIR = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "marks_sources", "mods_data")
RUNES_CATALOG_PATH = os.path.join(MODS_DATA_DIR, "runes.json")
SEARCH_RESULT_LIMIT = 12
TRAVEL_TIMEOUT_MS = 20000
WINDOW_GEOMETRY_SAVE_THROTTLE_MS = 750
DEFAULT_WINDOW_WIDTH = 760
DEFAULT_WINDOW_HEIGHT = 860
WORKSPACE_OVERVIEW = "overview"
WORKSPACE_RULES = "rules"
WORKSPACE_PROFILES = "profiles"
RULES_WORKSPACE_BUY = "buy"
RULES_WORKSPACE_SELL = "sell"
RULES_WORKSPACE_CLEANUP = "cleanup"
RULES_WORKSPACE_DESTROY = "destroy"
RULES_WORKSPACE_PROTECTIONS = "protections"
MULTIBOX_REMOTE_TIMEOUT_MS = 45000
MULTIBOX_EXECUTE_REMOTE_TIMEOUT_MS = 180000
MULTIBOX_REMOTE_IDLE_WAIT_TIMEOUT_MS = 120000
MULTIBOX_REMOTE_STATUS_UPDATE_INTERVAL_MS = 5000
MERCHANT_SELL_CONFIRM_TIMEOUT_MS = 1500
DESTROY_CONFIRM_TIMEOUT_MS = 1200
PREVIEW_DIFF_ROW_LIMIT = 8
INSTANT_DESTROY_POLL_MS = 400
STACKABLE_DESTROY_MAX_STACK_SIZE = 250
INVENTORY_BAG_IDS: tuple[int, ...] = (1, 2, 3, 4)
PROFILE_WINDOW_GEOMETRY_KEYS: tuple[str, ...] = (
    "window_x",
    "window_y",
    "window_width",
    "window_height",
    "window_collapsed",
)
SHARED_PROFILE_SCHEMA = "merchant_rules_shared_profile_v1"
SHARED_PROFILE_SCHEMA_VERSION = 1
FAILED_PROFILE_SNAPSHOT_LIMIT = 3

MERCHANT_TYPE_TRAVEL = "travel"
MERCHANT_TYPE_MERCHANT = "merchant"
MERCHANT_TYPE_MATERIALS = "material_trader"
MERCHANT_TYPE_RUNE_TRADER = "rune_trader"
MERCHANT_TYPE_RARE_MATERIALS = "rare_material_trader"
MERCHANT_TYPE_INVENTORY = "inventory"
MERCHANT_TYPE_STORAGE = "storage"

BUY_KIND_MERCHANT_STOCK = "merchant_stock_target"
BUY_KIND_MATERIAL_TARGET = "buy_material_target"
BUY_KIND_RUNE_TRADER_TARGET = "buy_rune_trader_target"
LEGACY_BUY_KIND_ID_KITS = "restock_id_kits"
LEGACY_BUY_KIND_SALVAGE_KITS = "restock_salvage_kits"
LEGACY_BUY_KIND_ECTO = "buy_ectoplasm"

SELL_KIND_COMMON_MATERIALS = "sell_common_materials"
SELL_KIND_EXPLICIT_MODELS = "sell_explicit_models"
SELL_KIND_WEAPONS = "sell_weapons"
SELL_KIND_ARMOR = "sell_armor"
DESTROY_KIND_MATERIALS = "destroy_materials"
DESTROY_KIND_EXPLICIT_MODELS = "destroy_explicit_models"
DESTROY_KIND_WEAPONS = "destroy_weapons"
DESTROY_KIND_ARMOR = "destroy_armor"
LEGACY_SELL_KIND_WEAPONS_BY_RARITY = "sell_weapons_by_rarity"
LEGACY_SELL_KIND_ARMOR_BY_RARITY = "sell_armor_by_rarity"
LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS = "sell_identified_nonsalvageable_golds"

BUY_RULE_KINDS = [
    BUY_KIND_MERCHANT_STOCK,
    BUY_KIND_MATERIAL_TARGET,
    BUY_KIND_RUNE_TRADER_TARGET,
]

SELL_RULE_KINDS = [
    SELL_KIND_COMMON_MATERIALS,
    SELL_KIND_EXPLICIT_MODELS,
    SELL_KIND_WEAPONS,
    SELL_KIND_ARMOR,
]

DESTROY_RULE_KINDS = [
    DESTROY_KIND_WEAPONS,
    DESTROY_KIND_ARMOR,
    DESTROY_KIND_EXPLICIT_MODELS,
    DESTROY_KIND_MATERIALS,
]

BUY_RULE_WORKSPACE_ORDER: tuple[str, ...] = (
    BUY_KIND_MERCHANT_STOCK,
    BUY_KIND_MATERIAL_TARGET,
    BUY_KIND_RUNE_TRADER_TARGET,
)

SELL_RULE_WORKSPACE_ORDER: tuple[str, ...] = (
    SELL_KIND_WEAPONS,
    SELL_KIND_ARMOR,
    SELL_KIND_EXPLICIT_MODELS,
    SELL_KIND_COMMON_MATERIALS,
)

DESTROY_RULE_WORKSPACE_ORDER: tuple[str, ...] = (
    DESTROY_KIND_WEAPONS,
    DESTROY_KIND_ARMOR,
    DESTROY_KIND_EXPLICIT_MODELS,
    DESTROY_KIND_MATERIALS,
)

BUY_KIND_LABELS = {
    BUY_KIND_MERCHANT_STOCK: "Maintain Merchant Stock",
    BUY_KIND_MATERIAL_TARGET: "Maintain Crafting Materials",
    BUY_KIND_RUNE_TRADER_TARGET: "Maintain Runes & Insignias",
}

BUY_RULE_WORKSPACE_LABELS = {
    BUY_KIND_MERCHANT_STOCK: "Merchant Stock",
    BUY_KIND_MATERIAL_TARGET: "Materials",
    BUY_KIND_RUNE_TRADER_TARGET: "Runes & Insignias",
}

SELL_KIND_LABELS = {
    SELL_KIND_COMMON_MATERIALS: "Sell Materials",
    SELL_KIND_EXPLICIT_MODELS: "Sell Specific Items",
    SELL_KIND_WEAPONS: "Sell Weapons",
    SELL_KIND_ARMOR: "Sell Armor",
}

DESTROY_KIND_LABELS = {
    DESTROY_KIND_MATERIALS: "Destroy Materials",
    DESTROY_KIND_EXPLICIT_MODELS: "Destroy Specific Items",
    DESTROY_KIND_WEAPONS: "Destroy Weapons",
    DESTROY_KIND_ARMOR: "Destroy Armor",
}

SELL_RULE_WORKSPACE_LABELS = {
    SELL_KIND_WEAPONS: "Weapons",
    SELL_KIND_ARMOR: "Armor",
    SELL_KIND_EXPLICIT_MODELS: "Items",
    SELL_KIND_COMMON_MATERIALS: "Materials",
}

CLEANUP_WORKSPACE_LABEL = "Cleanup / Xunlai"

DESTROY_RULE_WORKSPACE_LABELS = {
    DESTROY_KIND_WEAPONS: "Weapons",
    DESTROY_KIND_ARMOR: "Armor",
    DESTROY_KIND_EXPLICIT_MODELS: "Items",
    DESTROY_KIND_MATERIALS: "Materials",
}

PROTECTION_FILTER_ALL = "all"
PROTECTION_FILTER_MODELS = "models"
PROTECTION_FILTER_WEAPON_TYPES = "weapon_types"
PROTECTION_FILTER_REQUIREMENTS = "requirements"
PROTECTION_FILTER_WEAPON_MODS = "weapon_mods"
PROTECTION_FILTER_RUNES = "runes"
PROTECTION_OWNER_FILTER_OPTIONS: tuple[tuple[str, str], ...] = (
    (PROTECTION_FILTER_ALL, "All Owners"),
    (SELL_KIND_WEAPONS, "Weapons"),
    (SELL_KIND_ARMOR, "Armor"),
)
PROTECTION_TYPE_FILTER_OPTIONS: tuple[tuple[str, str], ...] = (
    (PROTECTION_FILTER_ALL, "All Types"),
    (PROTECTION_FILTER_MODELS, "Models"),
    (PROTECTION_FILTER_WEAPON_TYPES, "Weapon Types"),
    (PROTECTION_FILTER_REQUIREMENTS, "Requirements"),
    (PROTECTION_FILTER_WEAPON_MODS, "Weapon Mods"),
    (PROTECTION_FILTER_RUNES, "Runes / Insignias"),
)
SELL_PROTECTION_ANCHOR_MODELS = "models"
SELL_PROTECTION_ANCHOR_WEAPON_TYPES = "weapon_types"
SELL_PROTECTION_ANCHOR_REQUIREMENTS = "requirements"
SELL_PROTECTION_ANCHOR_WEAPON_MODS = "weapon_mods"
SELL_PROTECTION_ANCHOR_RUNES = "runes"
SELL_PROTECTION_TARGET_KEY_ALL_WEAPONS_REQUIREMENT = "__all_weapons_requirement__"

MERCHANT_TYPE_LABELS = {
    MERCHANT_TYPE_TRAVEL: "Travel",
    MERCHANT_TYPE_MERCHANT: "Merchant",
    MERCHANT_TYPE_MATERIALS: "Material Trader",
    MERCHANT_TYPE_RUNE_TRADER: "Rune Trader",
    MERCHANT_TYPE_RARE_MATERIALS: "Rare Material Trader",
    MERCHANT_TYPE_INVENTORY: "Inventory",
    MERCHANT_TYPE_STORAGE: "Xunlai Storage",
}

TRAVEL_PINNED_OUTPOST_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Embark Beach", ("Embark Beach",)),
    ("Great Temple of Balthazar", ("Great Temple of Balthazar",)),
    ("Kaineng Center", ("Kaineng Center",)),
    ("Kamadan, Jewel of Istan", ("Kamadan, Jewel of Istan", "Kamadan Jewel of Istan")),
    ("Lion's Arch", ("Lion's Arch", "Lions Arch")),
)

BUY_KIND_TO_MERCHANT_TYPE = {
    BUY_KIND_MERCHANT_STOCK: MERCHANT_TYPE_MERCHANT,
    BUY_KIND_MATERIAL_TARGET: MERCHANT_TYPE_MATERIALS,
    BUY_KIND_RUNE_TRADER_TARGET: MERCHANT_TYPE_RUNE_TRADER,
}

SELL_KIND_TO_MERCHANT_TYPE = {
    SELL_KIND_COMMON_MATERIALS: MERCHANT_TYPE_MATERIALS,
    SELL_KIND_EXPLICIT_MODELS: MERCHANT_TYPE_MERCHANT,
    SELL_KIND_WEAPONS: MERCHANT_TYPE_MERCHANT,
    SELL_KIND_ARMOR: MERCHANT_TYPE_MERCHANT,
}

ECTOPLASM_MODEL_ID = int(ModelID.Glob_Of_Ectoplasm.value)
SALVAGE_KIT_MODEL_ID = int(ModelID.Salvage_Kit.value)
MATERIAL_BATCH_SIZE = 10
MAX_WEAPON_REQUIREMENT = 13
COMMON_CRAFTING_MATERIAL_MODEL_IDS: frozenset[int] = frozenset({
    921, 925, 929, 933, 934, 940, 946, 948, 953, 954, 955,
})
RARE_CRAFTING_MATERIAL_MODEL_IDS: frozenset[int] = frozenset({
    922, 923, 926, 927, 928, 930, 931, 932, 935, 936, 937, 938, 939,
    941, 942, 943, 944, 945, 949, 950, 951, 952, 956, 6532, 6533,
})
ALL_CRAFTING_MATERIAL_MODEL_IDS: frozenset[int] = frozenset(
    set(COMMON_CRAFTING_MATERIAL_MODEL_IDS) | set(RARE_CRAFTING_MATERIAL_MODEL_IDS)
)
OUTPOST_SERVICE_SEARCH_MAX_DIST = 15_000.0
MERCHANT_NAME_QUERY = "[Merchant]"
MATERIAL_TRADER_NAME_QUERY = "[Material Trader]"
RARE_MATERIAL_TRADER_NAME_QUERY = "[Rare Material Trader]"
RUNE_TRADER_NAME_QUERY = "Rune Trader"
XUNLAI_AGENT_NAME_QUERY = "Xunlai Agent"
XUNLAI_CHEST_NAME_QUERY = "Xunlai Chest"
XUNLAI_AGENT_MODEL_IDS: tuple[int, ...] = (220, 221, 3287)
XUNLAI_CHEST_MODEL_ID = 5001
RUNE_STANDALONE_KIND = "rune"
WEAPON_MOD_STANDALONE_KIND = "weapon_mod"
RARITY_OPTION_ORDER: tuple[tuple[str, str], ...] = (
    ("white", "White"),
    ("blue", "Blue"),
    ("purple", "Purple"),
    ("gold", "Gold"),
    ("green", "Green"),
)
SUPPORTED_MAP_RUNE_TRADER_SELECTORS: dict[int, str] = {}
ACTION_TYPE_LABELS = {
    "buy": "Buy",
    "sell": "Sell",
    "destroy": "Destroy",
    "travel": "Travel",
    "withdraw": "Withdraw",
    "deposit": "Deposit",
}
STORAGE_PLAN_STATE_NOT_NEEDED = "not_needed"
STORAGE_PLAN_STATE_NEEDS_EXACT_SCAN = "needs_exact_scan"
STORAGE_PLAN_STATE_EXACT_READY = "exact_ready"
STORAGE_TRANSFER_WITHDRAW = "withdraw"
STORAGE_TRANSFER_DEPOSIT = "deposit"
STOCK_KEY_MODEL_PREFIX = "model:"
STOCK_KEY_IDENTIFIER_PREFIX = "identifier:"
MERCHANT_RULES_OPCODE_RELOAD_PROFILE = 1
MERCHANT_RULES_OPCODE_PREVIEW = 2
MERCHANT_RULES_OPCODE_EXECUTE = 3
MERCHANT_RULES_OPCODE_STATUS_RESULT = 100
MERCHANT_RULES_OPCODE_PREVIEW_RESULT = 101
MERCHANT_RULES_OPCODE_EXECUTE_RESULT = 102
MERCHANT_RULES_OPCODE_ERROR_RESULT = 199
PLAN_STATE_WILL_EXECUTE = "will execute"
PLAN_STATE_CONDITIONAL = "conditional"
PLAN_STATE_SKIPPED = "skipped"
PROJECTED_PREVIEW_CONTEXT_COORDS = (0.0, 0.0)
UI_COLOR_INFO = (0.30, 0.72, 1.00, 1.0)
UI_COLOR_SUCCESS = (0.18, 0.86, 0.40, 1.0)
UI_COLOR_WARNING = (1.00, 0.76, 0.20, 1.0)
UI_COLOR_DANGER = (0.97, 0.29, 0.29, 1.0)
UI_COLOR_MUTED = (0.68, 0.71, 0.76, 1.0)
UI_COLOR_SUBTLE = (0.90, 0.92, 0.96, 1.0)
UI_COLOR_SECONDARY_TEXT = (0.84, 0.86, 0.90, 1.0)
UI_COLOR_SECTION_HEADING = (0.79, 0.81, 0.86, 1.0)
UI_COLOR_TAB_ACTIVE = (0.18, 0.86, 0.40, 1.0)
UI_COLOR_TEAL = (0.14, 0.79, 0.76, 1.0)
UI_COLOR_INDIGO = (0.48, 0.62, 1.00, 1.0)
UI_COLOR_PURPLE_ACCENT = (0.79, 0.57, 0.96, 1.0)
RARITY_TEXT_COLORS = {
    "white": (0.96, 0.97, 0.99, 1.0),
    "blue": (0.34, 0.70, 1.00, 1.0),
    "purple": (0.79, 0.57, 0.96, 1.0),
    "gold": (1.00, 0.82, 0.24, 1.0),
    "green": (0.24, 0.90, 0.44, 1.0),
}
RULE_KIND_PRESENTATION: dict[str, tuple[str, tuple[float, float, float, float]]] = {
    BUY_KIND_MERCHANT_STOCK: ("Stock", UI_COLOR_INFO),
    BUY_KIND_MATERIAL_TARGET: ("Materials", UI_COLOR_TEAL),
    BUY_KIND_RUNE_TRADER_TARGET: ("Runes", UI_COLOR_PURPLE_ACCENT),
    SELL_KIND_COMMON_MATERIALS: ("Materials", UI_COLOR_TEAL),
    SELL_KIND_EXPLICIT_MODELS: ("Items", UI_COLOR_INDIGO),
    SELL_KIND_WEAPONS: ("Weapons", UI_COLOR_SUCCESS),
    SELL_KIND_ARMOR: ("Armor", UI_COLOR_PURPLE_ACCENT),
    DESTROY_KIND_MATERIALS: ("Destroy", UI_COLOR_DANGER),
    DESTROY_KIND_EXPLICIT_MODELS: ("Destroy", UI_COLOR_DANGER),
    DESTROY_KIND_WEAPONS: ("Destroy", UI_COLOR_DANGER),
    DESTROY_KIND_ARMOR: ("Destroy", UI_COLOR_DANGER),
}


def _color_tuple_to_imgui_u32(color: tuple[float, float, float, float], *, alpha_scale: float = 1.0) -> int:
    rgba: list[int] = []
    for component_index, component in enumerate(color[:4]):
        value = float(component)
        if value <= 1.0:
            channel = int(round(max(0.0, min(1.0, value)) * 255.0))
        else:
            channel = int(round(max(0.0, min(255.0, value))))
        if component_index == 3:
            channel = int(round(max(0.0, min(255.0, channel * max(0.0, alpha_scale)))))
        rgba.append(channel)
    while len(rgba) < 4:
        rgba.append(255)
    red, green, blue, alpha = rgba
    return ((alpha & 0xFF) << 24) | ((blue & 0xFF) << 16) | ((green & 0xFF) << 8) | (red & 0xFF)


try:
    MOD_DB = ModDatabase.load(MODS_DATA_DIR)
    MOD_DB_LOAD_ERROR = ""
except Exception as exc:
    MOD_DB = ModDatabase()
    MOD_DB_LOAD_ERROR = f"Modifier data load failed: {exc}"


WEAPON_ITEM_TYPE_OPTIONS: tuple[tuple[ItemType, str], ...] = (
    (ItemType.Axe, "Axe"),
    (ItemType.Bow, "Bow"),
    (ItemType.Daggers, "Daggers"),
    (ItemType.Hammer, "Hammer"),
    (ItemType.Offhand, "Offhand / Focus"),
    (ItemType.Scythe, "Scythe"),
    (ItemType.Shield, "Shield"),
    (ItemType.Spear, "Spear"),
    (ItemType.Staff, "Staff"),
    (ItemType.Sword, "Sword"),
    (ItemType.Wand, "Wand"),
)
WEAPON_ITEM_TYPE_IDS: set[int] = {int(item_type.value) for item_type, _label in WEAPON_ITEM_TYPE_OPTIONS}
WEAPON_ITEM_TYPE_NAMES: dict[int, str] = {
    int(item_type.value): label
    for item_type, label in WEAPON_ITEM_TYPE_OPTIONS
}
WEAPON_LIKE_ITEM_TYPES: frozenset[ItemType] = frozenset(item_type for item_type, _label in WEAPON_ITEM_TYPE_OPTIONS)
ARMOR_PIECE_TYPES: frozenset[ItemType] = frozenset({
    ItemType.Headpiece,
    ItemType.Chestpiece,
    ItemType.Gloves,
    ItemType.Leggings,
    ItemType.Boots,
    ItemType.Salvage,
})
WEAPON_CATALOG_ITEM_TYPE_TOKENS: frozenset[str] = frozenset({
    "axe",
    "bow",
    "daggers",
    "focus",
    "hammer",
    "offhand",
    "scythe",
    "shield",
    "spear",
    "staff",
    "sword",
    "wand",
})
MODEL_ID_ATTRIBUTE_FALLBACK_LABELS: dict[str, str] = {
    "Air": "Air Magic",
    "AirMagic": "Air Magic",
    "Blood": "Blood Magic",
    "BloodMagic": "Blood Magic",
    "Channeling": "Channeling Magic",
    "ChannelingMagic": "Channeling Magic",
    "Communing": "Communing",
    "Curses": "Curses",
    "Death": "Death Magic",
    "DeathMagic": "Death Magic",
    "Divine": "Divine Favor",
    "DivineFavor": "Divine Favor",
    "Domination": "Domination Magic",
    "DominationMagic": "Domination Magic",
    "Earth": "Earth Magic",
    "EarthMagic": "Earth Magic",
    "Energy_Storage": "Energy Storage",
    "EnergyStorage": "Energy Storage",
    "Fast_Casting": "Fast Casting",
    "FastCasting": "Fast Casting",
    "Fire": "Fire Magic",
    "FireMagic": "Fire Magic",
    "Healing": "Healing Prayers",
    "HealingPrayers": "Healing Prayers",
    "Illusion": "Illusion Magic",
    "IllusionMagic": "Illusion Magic",
    "Inspiration": "Inspiration Magic",
    "InspirationMagic": "Inspiration Magic",
    "Protection": "Protection Prayers",
    "ProtectionPrayers": "Protection Prayers",
    "Restoration": "Restoration Magic",
    "RestorationMagic": "Restoration Magic",
    "Smiting": "Smiting Prayers",
    "SmitingPrayers": "Smiting Prayers",
    "Soul_Reaping": "Soul Reaping",
    "SoulReaping": "Soul Reaping",
    "Spawning": "Spawning Power",
    "SpawningPower": "Spawning Power",
    "Water": "Water Magic",
    "WaterMagic": "Water Magic",
}
MODEL_ID_ATTRIBUTE_FALLBACK_SUFFIX_KEYS: tuple[str, ...] = tuple(
    sorted(MODEL_ID_ATTRIBUTE_FALLBACK_LABELS.keys(), key=len, reverse=True)
)
ARMOR_CATALOG_ITEM_TYPES: frozenset[str] = frozenset({
    "headpiece",
    "chestpiece",
    "gloves",
    "leggings",
    "boots",
})
ARMOR_SALVAGE_CATALOG_NAME_FRAGMENTS: tuple[str, ...] = (
    "armor",
    "robe",
    "vest",
    "vestments",
    "garb",
    "harness",
    "headpiece",
    "helm",
    "helmet",
    "hood",
    "mask",
    "gloves",
    "gauntlets",
    "leggings",
    "boots",
    "shoes",
    "sandals",
    "coat",
    "tunic",
    "raiment",
    "attire",
    "cape",
    "plating",
    "wraps",
    "wrappings",
    "jerkin",
    "sleeves",
    "tattoo",
    "tattoos",
    "cowl",
)
WEAPON_MOD_CATALOG_NAME_FRAGMENTS: tuple[str, ...] = (
    "axe grip",
    "axe haft",
    "bow grip",
    "bow string",
    "dagger handle",
    "dagger tang",
    "focus core",
    "hammer grip",
    "hammer haft",
    "inscription",
    "scythe grip",
    "scythe snathe",
    "shield handle",
    "spear grip",
    "spearhead",
    "staff head",
    "staff wrapping",
    "sword hilt",
    "sword pommel",
    "wand wrapping",
)
ARMOR_RUNE_CATALOG_NAME_TOKENS: frozenset[str] = frozenset({
    "rune",
    "insignia",
})


@dataclass
class MaterialTarget:
    model_id: int = 0
    target_count: int = 0
    max_per_run: int = 0


@dataclass
class MerchantStockTarget:
    model_id: int = 0
    target_count: int = 0
    max_per_run: int = 0


@dataclass
class RuneTraderTarget:
    identifier: str = ""
    target_count: int = 0
    max_per_run: int = 0


@dataclass
class WhitelistTarget:
    model_id: int = 0
    keep_count: int = 0
    deposit_to_storage: bool = False


@dataclass
class BuyRule:
    enabled: bool = False
    kind: str = BUY_KIND_MERCHANT_STOCK
    merchant_type: str = MERCHANT_TYPE_MERCHANT
    model_id: int = 0
    target_count: int = 0
    max_per_run: int = 0
    merchant_stock_targets: list[MerchantStockTarget] = field(default_factory=list)
    material_targets: list[MaterialTarget] = field(default_factory=list)
    rune_targets: list[RuneTraderTarget] = field(default_factory=list)
    name: str = ""


@dataclass
class WeaponRequirementRule:
    model_id: int = 0
    min_requirement: int = 0
    max_requirement: int = 0


@dataclass
class SellRule:
    enabled: bool = False
    kind: str = SELL_KIND_EXPLICIT_MODELS
    merchant_type: str = MERCHANT_TYPE_MERCHANT
    rule_id: str = ""
    model_ids: list[int] = field(default_factory=list)
    keep_count: int = 0
    whitelist_targets: list[WhitelistTarget] = field(default_factory=list)
    rarities: dict[str, bool] = field(default_factory=dict)
    blacklist_model_ids: list[int] = field(default_factory=list)
    blacklist_item_type_ids: list[int] = field(default_factory=list)
    all_weapons_min_requirement: int = 0
    all_weapons_max_requirement: int = 0
    protected_weapon_requirement_rules: list[WeaponRequirementRule] = field(default_factory=list)
    protected_weapon_mod_identifiers: list[str] = field(default_factory=list)
    protected_rune_identifiers: list[str] = field(default_factory=list)
    skip_customized: bool = True
    skip_unidentified: bool = True
    include_standalone_runes: bool = False
    deposit_protected_matches: bool = False
    name: str = ""


@dataclass
class DestroyRule:
    enabled: bool = False
    kind: str = DESTROY_KIND_EXPLICIT_MODELS
    model_ids: list[int] = field(default_factory=list)
    keep_count: int = 0
    whitelist_targets: list[WhitelistTarget] = field(default_factory=list)
    rarities: dict[str, bool] = field(default_factory=dict)
    name: str = ""


@dataclass
class CleanupTarget:
    model_id: int = 0
    keep_on_character: int = 0


@dataclass
class CleanupProtectionSource:
    sell_rule_id: str = ""


@dataclass
class ExecutionPlanEntry:
    action_type: str
    merchant_type: str
    label: str
    quantity: int
    state: str
    reason: str = ""
    model_id: int = 0


@dataclass
class ProtectionHubEntry:
    source_label: str
    filter_key: str
    protection_type_label: str
    value_label: str
    value_sort_key: str
    owner_rule_index: int
    owner_rule_kind: str
    owner_rule_kind_label: str
    owner_rule_label: str
    owner_rule_enabled: bool
    owner_rule_order: int
    search_text: str
    subsection_anchor: str = ""
    target_key: str = ""
    requires_advanced: bool = False


@dataclass
class SellProtectionJumpTarget:
    owner_rule_index: int
    owner_rule_kind: str
    subsection_anchor: str
    target_key: str = ""
    requires_advanced: bool = False
    force_rule_open: bool = True
    force_advanced_open: bool = False
    pending_rule_scroll: bool = True
    pending_outer_scroll: bool = True
    pending_inner_scroll: bool = False
    ignore_interaction_until_mouse_release: bool = True


@dataclass
class InventoryItemInfo:
    item_id: int
    model_id: int
    name: str
    quantity: int
    value: int
    item_type_id: int
    item_type_name: str
    rarity: str
    identified: bool
    salvageable: bool
    is_customized: bool
    is_inscribable: bool
    is_material: bool
    is_rare_material: bool
    is_weapon_like: bool
    is_armor_piece: bool
    requirement: int = 0
    standalone_kind: str = ""
    rune_identifiers: list[str] = field(default_factory=list)
    weapon_mod_identifiers: list[str] = field(default_factory=list)


@dataclass
class PlannedMerchantBuy:
    model_id: int
    quantity: int
    label: str


@dataclass
class PlannedMaterialBuy:
    merchant_type: str
    model_id: int
    quantity: int
    label: str
    batch_size: int = 1


@dataclass
class PlannedMaterialSale:
    merchant_type: str
    item_id: int
    model_id: int
    label: str
    batches_to_sell: int
    quantity_to_sell: int
    batch_size: int = MATERIAL_BATCH_SIZE


@dataclass
class PlannedTraderSale:
    item_id: int
    model_id: int
    label: str


@dataclass
class PlannedTraderBuy:
    identifier: str
    quantity: int
    label: str


@dataclass
class StockLocationCounts:
    key: str
    label: str
    inventory_count: int = 0
    storage_count: int = 0
    combined_count: int = 0
    exact: bool = False


@dataclass
class PlannedStorageTransfer:
    direction: str
    key: str
    label: str
    item_id: int
    quantity: int
    model_id: int = 0


@dataclass(frozen=True)
class DestroySplitDestination:
    bag_id: int
    slot: int
    destination_item_id: int = 0


@dataclass
class PlannedDestroyAction:
    item_id: int
    model_id: int
    label: str
    quantity_to_destroy: int
    source_quantity: int
    keep_quantity: int = 0
    requires_split: bool = False


@dataclass
class PlanResult:
    entries: list[ExecutionPlanEntry] = field(default_factory=list)
    supported_map: bool = False
    supported_reason: str = ""
    coords: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    travel_to_outpost_id: int = 0
    travel_to_outpost_name: str = ""
    merchant_stock_buys: list[PlannedMerchantBuy] = field(default_factory=list)
    material_buys: list[PlannedMaterialBuy] = field(default_factory=list)
    rune_trader_buys: list[PlannedTraderBuy] = field(default_factory=list)
    material_sales: list[PlannedMaterialSale] = field(default_factory=list)
    storage_transfers: list[PlannedStorageTransfer] = field(default_factory=list)
    cleanup_transfers: list[PlannedStorageTransfer] = field(default_factory=list)
    destroy_actions: list[PlannedDestroyAction] = field(default_factory=list)
    destroy_item_ids: list[int] = field(default_factory=list)
    merchant_sell_item_ids: list[int] = field(default_factory=list)
    rune_trader_sales: list[PlannedTraderSale] = field(default_factory=list)
    storage_plan_state: str = STORAGE_PLAN_STATE_NOT_NEEDED
    storage_exact: bool = False
    inventory_snapshot_captured: bool = False
    inventory_model_counts: dict[int, int] = field(default_factory=dict)
    inventory_item_count: int = 0
    has_actions: bool = False


@dataclass
class MultiboxAccountStatus:
    email: str
    display_name: str = ""
    state: str = "idle"
    status_label: str = ""
    summary: str = ""
    detail: str = ""
    primary_count: int = 0
    secondary_count: int = 0
    success: bool = False


@dataclass
class SharedProfileSummary:
    path: str
    display_name: str
    filename: str
    saved_at_label: str = ""
    saved_at_unix_ms: int = 0
    payload: dict[str, object] = field(default_factory=dict)
    serialized_payload: str = ""


@dataclass(frozen=True)
class ParsedInventoryModifiers:
    requirement: int = 0
    standalone_kind: str = ""
    rune_identifiers: tuple[str, ...] = field(default_factory=tuple)
    weapon_mod_identifiers: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class InventoryModifierCacheEntry:
    signature: tuple[object, ...]
    parsed: ParsedInventoryModifiers


@dataclass
class ExecutionPhaseOutcome:
    label: str
    measure_label: str = "actions"
    attempted: int = 0
    completed: int = 0
    unavailable: int = 0
    quote_failures: int = 0
    timeout_failures: int = 0
    load_failures: int = 0
    gold_blocked: int = 0
    depleted: int = 0


def _default_rarity_flags() -> dict[str, bool]:
    return {
        "white": True,
        "blue": True,
        "purple": True,
        "gold": True,
        "green": False,
    }


def _normalize_rarity_flags(raw_value: object) -> dict[str, bool]:
    flags = _default_rarity_flags()
    if isinstance(raw_value, dict):
        for key, _label in RARITY_OPTION_ORDER:
            if key in raw_value:
                flags[key] = bool(raw_value.get(key, flags[key]))
    return flags


def _normalize_rarity_key(raw_value: str) -> str:
    return str(raw_value or "").strip().lower()


def _dedupe_identifiers(values: list[object]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        identifier = str(value or "").strip()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        unique.append(identifier)
    return unique


def _normalize_rule_name(raw_value: object) -> str:
    if raw_value is None:
        return ""
    normalized = " ".join(str(raw_value).replace("\r", " ").replace("\n", " ").split())
    return normalized.strip()


def _get_rarity_options_for_rule(rule_kind: str) -> tuple[tuple[str, str], ...]:
    if rule_kind in (SELL_KIND_ARMOR, DESTROY_KIND_ARMOR):
        return tuple((key, label) for key, label in RARITY_OPTION_ORDER if key != "green")
    return RARITY_OPTION_ORDER


def _safe_int(value: object, default: int = 0) -> int:
    try:
        if isinstance(value, str):
            return int(value.strip(), 0)
        return int(value)
    except Exception:
        return default


def _coerce_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def _sanitize_filename(value: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]+', "_", str(value or "").strip())
    return sanitized or "default"


def _normalize_shared_profile_display_name(raw_value: object) -> str:
    return _normalize_rule_name(raw_value)


def _strip_window_geometry_from_profile_payload(payload: object) -> dict[str, object]:
    raw_payload = dict(payload) if isinstance(payload, dict) else {}
    return {
        key: value
        for key, value in raw_payload.items()
        if key not in PROFILE_WINDOW_GEOMETRY_KEYS
    }


def _looks_like_merchant_rules_payload(raw_payload: object) -> bool:
    if not isinstance(raw_payload, dict):
        return False
    return any(
        key in raw_payload
        for key in (
            "buy_rules",
            "sell_rules",
            "destroy_rules",
            "cleanup_targets",
            "cleanup_protection_sources",
            "auto_cleanup_on_outpost_entry",
            "auto_travel_enabled",
            "target_outpost_id",
            "favorite_outpost_ids",
            "debug_logging",
        )
    )


def _normalize_outpost_match_text(raw_value: object) -> str:
    normalized = str(raw_value or "").strip().lower()
    if not normalized:
        return ""
    normalized = normalized.replace("’", "").replace("'", "").replace(",", "")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _normalize_multibox_account_email(raw_value: object) -> str:
    return str(raw_value or "").strip().lower()


def _hash_account_key(value: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        return ""
    return md5(safe_value.encode()).hexdigest()[:8]


def _get_config_filename_for_account_key(account_key: str) -> str:
    hashed_key = _hash_account_key(account_key)
    if hashed_key:
        return f"MerchantRules_{hashed_key}.json"
    return "MerchantRules_default.json"


def _get_config_path_for_account_key(account_key: str) -> str:
    return os.path.join(CONFIG_DIR, _get_config_filename_for_account_key(account_key))


def _format_model_ids(model_ids: list[int]) -> str:
    return ", ".join(str(model_id) for model_id in model_ids)


def _parse_model_ids(raw: str) -> list[int]:
    parsed: list[int] = []
    for part in str(raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            parsed.append(int(part, 0))
        except ValueError:
            continue
    return parsed


def _parse_batch_model_ids(raw: str) -> tuple[list[int], int]:
    parsed: list[int] = []
    invalid_count = 0
    for part in re.split(r"[\s,;]+", str(raw or "").strip()):
        token = str(part or "").strip()
        if not token:
            continue
        try:
            parsed.append(int(token, 0))
        except ValueError:
            invalid_count += 1
    return _dedupe_model_ids(parsed), invalid_count


def _collect_model_ids_from_catalog_entries(entries: list[dict[str, object]]) -> list[int]:
    return _dedupe_model_ids([_safe_int(entry.get("model_id", 0), 0) for entry in entries])


def _collect_identifiers_from_catalog_entries(entries: list[dict[str, str]]) -> list[str]:
    return _dedupe_identifiers([str(entry.get("identifier", "")).strip() for entry in entries])


def _dedupe_model_ids(model_ids: list[int]) -> list[int]:
    unique: list[int] = []
    seen: set[int] = set()
    for value in model_ids:
        model_id = max(0, _safe_int(value, 0))
        if model_id <= 0 or model_id in seen:
            continue
        seen.add(model_id)
        unique.append(model_id)
    return unique


def _dedupe_weapon_item_type_ids(item_type_ids: list[object]) -> list[int]:
    unique: list[int] = []
    seen: set[int] = set()
    for value in item_type_ids:
        item_type_id = _safe_int(value, 0)
        if item_type_id not in WEAPON_ITEM_TYPE_IDS or item_type_id in seen:
            continue
        seen.add(item_type_id)
        unique.append(item_type_id)
    return unique


def _resolve_model_id_value(raw_value: object) -> int:
    if isinstance(raw_value, str):
        candidate = raw_value.strip()
        if not candidate:
            return 0
        if candidate.startswith("ModelID."):
            enum_name = candidate.split(".", 1)[1].strip()
            enum_value = getattr(ModelID, enum_name, None)
            if enum_value is not None:
                try:
                    return int(enum_value.value)
                except Exception:
                    return _safe_int(enum_value, 0)
        return _safe_int(candidate, 0)
    return _safe_int(raw_value, 0)


def _normalize_catalog_search_text(raw_value: object) -> str:
    text = str(raw_value or "").strip().lower()
    if not text:
        return ""
    text = unquote(text)
    text = text.replace("_", " ")
    text = re.sub(r"\.[a-z0-9]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _build_catalog_alias_labels(name: object, skin: object = "", wiki_url: object = "") -> dict[str, str]:
    alias_labels: dict[str, str] = {}

    def _add_alias(raw_alias: object, display_label: object = ""):
        normalized = _normalize_catalog_search_text(raw_alias)
        if not normalized:
            return
        display = str(display_label or raw_alias or "").strip()
        if not display:
            display = normalized.title()
        alias_labels.setdefault(normalized, display)

    safe_name = str(name or "").strip()
    if safe_name:
        _add_alias(safe_name, safe_name)

    safe_skin = str(skin or "").strip()
    if safe_skin:
        skin_label = os.path.splitext(os.path.basename(safe_skin))[0].strip()
        if skin_label:
            _add_alias(skin_label, skin_label)

    safe_wiki_url = str(wiki_url or "").strip()
    if safe_wiki_url:
        wiki_stem = safe_wiki_url.rsplit("/", 1)[-1].split("?", 1)[0].split("#", 1)[0].strip()
        wiki_label = unquote(wiki_stem).replace("_", " ").strip()
        if wiki_label:
            _add_alias(wiki_label, wiki_label)

    return alias_labels


def _humanize_model_id_enum_name(raw_name: object) -> str:
    text = str(raw_name or "").strip()
    if not text:
        return ""
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_mirrored_item_priority(item_type: object) -> int:
    normalized_type = str(item_type or "").strip().lower()
    if normalized_type in {
        "axe",
        "bow",
        "daggers",
        "hammer",
        "offhand",
        "scythe",
        "shield",
        "spear",
        "staff",
        "sword",
        "wand",
        "headpiece",
        "chestpiece",
        "gloves",
        "leggings",
        "boots",
    }:
        return 10
    if normalized_type in {"rune_mod", "salvage"}:
        return 20
    return 30


MODEL_ID_FALLBACK_ITEM_TYPE_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("Daggers", "Daggers"),
    ("Scythe", "Scythe"),
    ("Shield", "Shield"),
    ("Spear", "Spear"),
    ("Staff", "Staff"),
    ("Sword", "Sword"),
    ("Hammer", "Hammer"),
    ("Focus", "Offhand"),
    ("Offhand", "Offhand"),
    ("Icon", "Offhand"),
    ("Prism", "Offhand"),
    ("Wand", "Wand"),
    ("Bow", "Bow"),
    ("Axe", "Axe"),
    ("Headpiece", "Headpiece"),
    ("Chestpiece", "Chestpiece"),
    ("Gloves", "Gloves"),
    ("Leggings", "Leggings"),
    ("Boots", "Boots"),
    ("SalvageKit", "Salvage"),
)


def _infer_model_id_fallback_item_type(enum_names: list[str], display_name: str) -> str:
    candidates = [display_name, *enum_names]
    for candidate in candidates:
        compact = re.sub(r"[^A-Za-z0-9]+", "", str(candidate or ""))
        normalized = _normalize_catalog_search_text(_humanize_model_id_enum_name(candidate))
        tokens = set(normalized.split())
        for suffix, item_type in MODEL_ID_FALLBACK_ITEM_TYPE_SUFFIXES:
            suffix_lower = suffix.lower()
            if compact.lower().endswith(suffix_lower) or suffix_lower in tokens:
                return item_type
    return ""


def _iter_model_id_enum_members() -> list[tuple[str, int]]:
    members = getattr(ModelID, "__members__", None)
    if isinstance(members, dict):
        raw_members = list(members.items())
    else:
        raw_members = [
            (name, getattr(ModelID, name))
            for name in dir(ModelID)
            if not name.startswith("_")
        ]

    resolved_members: list[tuple[str, int]] = []
    for raw_name, raw_value in raw_members:
        name = str(raw_name or "").strip()
        if not name:
            continue
        try:
            model_id = int(raw_value.value)
        except Exception:
            model_id = _safe_int(raw_value, 0)
        if model_id > 0:
            resolved_members.append((name, model_id))
    return resolved_members


def _iter_item_handling_catalog_entries(raw_catalog: object) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []

    def _walk(raw_value: object):
        if isinstance(raw_value, dict):
            if ("model_id" in raw_value or "ModelID" in raw_value) and ("name" in raw_value or "Name" in raw_value):
                entries.append(raw_value)
                return
            for child_value in raw_value.values():
                _walk(child_value)
        elif isinstance(raw_value, list):
            for child_value in raw_value:
                _walk(child_value)

    _walk(raw_catalog)
    return entries


def _is_common_crafting_material_model(model_id: object) -> bool:
    return max(0, _safe_int(model_id, 0)) in COMMON_CRAFTING_MATERIAL_MODEL_IDS


def _is_rare_crafting_material_model(model_id: object) -> bool:
    return max(0, _safe_int(model_id, 0)) in RARE_CRAFTING_MATERIAL_MODEL_IDS


def _is_crafting_material_model(model_id: object) -> bool:
    return max(0, _safe_int(model_id, 0)) in ALL_CRAFTING_MATERIAL_MODEL_IDS


def _get_material_batch_size_for_model(model_id: object) -> int:
    return MATERIAL_BATCH_SIZE if _is_common_crafting_material_model(model_id) else 1


def _normalize_weapon_requirement_level(value: object) -> int:
    return min(MAX_WEAPON_REQUIREMENT, max(0, _safe_int(value, 0)))


def _normalize_weapon_requirement_range(min_value: object, max_value: object) -> tuple[int, int]:
    min_requirement = _normalize_weapon_requirement_level(min_value)
    max_requirement = _normalize_weapon_requirement_level(max_value)
    if min_requirement > 0 and max_requirement > 0 and min_requirement > max_requirement:
        min_requirement, max_requirement = max_requirement, min_requirement
    return min_requirement, max_requirement


def _should_defer_weapon_requirement_range_commit(min_value: object, max_value: object, *, input_active: bool) -> bool:
    min_requirement = _normalize_weapon_requirement_level(min_value)
    max_requirement = _normalize_weapon_requirement_level(max_value)
    return bool(input_active and min_requirement > 0 and max_requirement > 0 and min_requirement > max_requirement)


def _get_last_imgui_item_active() -> bool:
    is_item_active = getattr(PyImGui, "is_item_active", None)
    if not callable(is_item_active):
        return False
    try:
        return bool(is_item_active())
    except Exception:
        return False


def _is_weapon_requirement_range_active(min_requirement: object, max_requirement: object) -> bool:
    normalized_min, normalized_max = _normalize_weapon_requirement_range(min_requirement, max_requirement)
    return normalized_min > 0 and normalized_max > 0


def _normalize_all_weapons_requirement_range_from_payload(entry: dict[str, object]) -> tuple[int, int]:
    raw_max_requirement = entry.get("all_weapons_max_requirement", 0)
    raw_min_requirement = entry.get(
        "all_weapons_min_requirement",
        1 if _normalize_weapon_requirement_level(raw_max_requirement) > 0 else 0,
    )
    return _normalize_weapon_requirement_range(raw_min_requirement, raw_max_requirement)


def _is_weapon_catalog_item_type(item_type: object) -> bool:
    normalized_type = str(item_type or "").strip().lower()
    if not normalized_type:
        return False
    tokens = [token for token in re.split(r"[^a-z]+", normalized_type) if token]
    return any(token in WEAPON_CATALOG_ITEM_TYPE_TOKENS for token in tokens)


def _is_armor_catalog_item_type(item_type: object) -> bool:
    return str(item_type or "").strip().lower() in ARMOR_CATALOG_ITEM_TYPES


def _is_weapon_mod_catalog_name(name: object) -> bool:
    normalized_name = _normalize_catalog_search_text(name)
    if not normalized_name:
        return False
    return any(fragment in normalized_name for fragment in WEAPON_MOD_CATALOG_NAME_FRAGMENTS)


def _is_armor_rune_catalog_name(name: object) -> bool:
    normalized_name = _normalize_catalog_search_text(name)
    if not normalized_name:
        return False
    tokens = [token for token in re.split(r"[^a-z]+", normalized_name) if token]
    return any(token in ARMOR_RUNE_CATALOG_NAME_TOKENS for token in tokens)


def _is_armor_salvage_catalog_name(name: object) -> bool:
    normalized_name = _normalize_catalog_search_text(name)
    if not normalized_name:
        return False
    return any(fragment in normalized_name for fragment in ARMOR_SALVAGE_CATALOG_NAME_FRAGMENTS)


def _normalize_material_targets(raw_targets: object) -> list[MaterialTarget]:
    normalized: list[MaterialTarget] = []
    seen_model_ids: set[int] = set()
    if not isinstance(raw_targets, list):
        return normalized

    for entry in raw_targets:
        if isinstance(entry, MaterialTarget):
            model_id = entry.model_id
            target_count = entry.target_count
            max_per_run = entry.max_per_run
        elif isinstance(entry, dict):
            model_id = entry.get("model_id", 0)
            target_count = entry.get("target_count", 0)
            max_per_run = entry.get("max_per_run", 0)
        else:
            continue

        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0 or safe_model_id in seen_model_ids:
            continue

        seen_model_ids.add(safe_model_id)
        normalized.append(
            MaterialTarget(
                model_id=safe_model_id,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )

    return normalized


def _normalize_merchant_stock_targets(raw_targets: object) -> list[MerchantStockTarget]:
    normalized: list[MerchantStockTarget] = []
    seen_model_ids: set[int] = set()
    if not isinstance(raw_targets, list):
        return normalized

    for entry in raw_targets:
        if isinstance(entry, MerchantStockTarget):
            model_id = entry.model_id
            target_count = entry.target_count
            max_per_run = entry.max_per_run
        elif isinstance(entry, dict):
            model_id = entry.get("model_id", 0)
            target_count = entry.get("target_count", 0)
            max_per_run = entry.get("max_per_run", 0)
        else:
            continue

        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0 or safe_model_id in seen_model_ids:
            continue

        seen_model_ids.add(safe_model_id)
        normalized.append(
            MerchantStockTarget(
                model_id=safe_model_id,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )

    return normalized


def _normalize_rune_identifier(identifier: object) -> str:
    return str(identifier or "").strip()


def _normalize_rune_trader_targets(raw_targets: object) -> list[RuneTraderTarget]:
    normalized: list[RuneTraderTarget] = []
    seen_identifiers: set[str] = set()
    if not isinstance(raw_targets, list):
        return normalized

    for entry in raw_targets:
        if isinstance(entry, RuneTraderTarget):
            identifier = entry.identifier
            target_count = entry.target_count
            max_per_run = entry.max_per_run
        elif isinstance(entry, dict):
            identifier = entry.get("identifier", "")
            target_count = entry.get("target_count", 0)
            max_per_run = entry.get("max_per_run", 0)
        else:
            continue

        safe_identifier = _normalize_rune_identifier(identifier)
        if not safe_identifier or safe_identifier in seen_identifiers:
            continue

        seen_identifiers.add(safe_identifier)
        normalized.append(
            RuneTraderTarget(
                identifier=safe_identifier,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )

    return normalized


def _normalize_whitelist_targets(raw_targets: object) -> list[WhitelistTarget]:
    normalized: list[WhitelistTarget] = []
    seen_model_ids: set[int] = set()
    if not isinstance(raw_targets, list):
        return normalized

    for entry in raw_targets:
        if isinstance(entry, WhitelistTarget):
            model_id = entry.model_id
            keep_count = entry.keep_count
            deposit_to_storage = bool(getattr(entry, "deposit_to_storage", False))
        elif isinstance(entry, dict):
            model_id = entry.get("model_id", 0)
            keep_count = entry.get("keep_count", 0)
            deposit_to_storage = bool(entry.get("deposit_to_storage", False))
        else:
            continue

        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0 or safe_model_id in seen_model_ids:
            continue

        seen_model_ids.add(safe_model_id)
        normalized.append(
            WhitelistTarget(
                model_id=safe_model_id,
                keep_count=max(0, _safe_int(keep_count, 0)),
                deposit_to_storage=bool(deposit_to_storage),
            )
        )

    return normalized


def _normalize_cleanup_targets(raw_targets: object) -> list[CleanupTarget]:
    normalized: list[CleanupTarget] = []
    seen_model_ids: set[int] = set()
    if not isinstance(raw_targets, list):
        return normalized

    for entry in raw_targets:
        if isinstance(entry, CleanupTarget):
            model_id = entry.model_id
            keep_on_character = entry.keep_on_character
        elif isinstance(entry, dict):
            model_id = entry.get("model_id", 0)
            keep_on_character = entry.get("keep_on_character", entry.get("keep_count", 0))
        else:
            continue

        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0 or safe_model_id in seen_model_ids:
            continue

        seen_model_ids.add(safe_model_id)
        normalized.append(
            CleanupTarget(
                model_id=safe_model_id,
                keep_on_character=max(0, _safe_int(keep_on_character, 0)),
            )
        )

    return normalized


def _normalize_cleanup_protection_sources(raw_sources: object) -> list[CleanupProtectionSource]:
    normalized: list[CleanupProtectionSource] = []
    seen_rule_ids: set[str] = set()
    if not isinstance(raw_sources, list):
        return normalized

    for entry in raw_sources:
        if isinstance(entry, CleanupProtectionSource):
            sell_rule_id = entry.sell_rule_id
        elif isinstance(entry, dict):
            sell_rule_id = entry.get("sell_rule_id", "")
        else:
            continue

        safe_rule_id = str(sell_rule_id or "").strip()
        if not safe_rule_id or safe_rule_id in seen_rule_ids:
            continue

        seen_rule_ids.add(safe_rule_id)
        normalized.append(CleanupProtectionSource(sell_rule_id=safe_rule_id))

    return normalized


def _serialize_whitelist_targets(raw_targets: object) -> list[dict[str, object]]:
    return [
        {
            "model_id": int(target.model_id),
            "keep_count": max(0, int(target.keep_count)),
            "deposit_to_storage": bool(getattr(target, "deposit_to_storage", False)),
        }
        for target in _normalize_whitelist_targets(raw_targets)
    ]


def _serialize_cleanup_targets(raw_targets: object) -> list[dict[str, int]]:
    return [
        {
            "model_id": int(target.model_id),
            "keep_on_character": max(0, int(target.keep_on_character)),
        }
        for target in _normalize_cleanup_targets(raw_targets)
    ]


def _serialize_cleanup_protection_sources(raw_sources: object) -> list[dict[str, str]]:
    return [
        {
            "sell_rule_id": str(source.sell_rule_id or "").strip(),
        }
        for source in _normalize_cleanup_protection_sources(raw_sources)
    ]


def _normalize_rule_id(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "", str(value or "").strip())


def _make_generated_rule_id(prefix: str, fallback_seed: object = "") -> str:
    safe_prefix = _normalize_rule_id(prefix) or "rule"
    seed = f"{safe_prefix}:{fallback_seed}:{time.time_ns()}"
    return f"{safe_prefix}_{md5(seed.encode()).hexdigest()[:10]}"


def _ensure_unique_rule_id(
    raw_value: object,
    *,
    seen_ids: set[str],
    prefix: str,
    fallback_seed: object = "",
) -> str:
    candidate = _normalize_rule_id(raw_value)
    if not candidate or candidate in seen_ids:
        candidate = _make_generated_rule_id(prefix, fallback_seed)
        while candidate in seen_ids:
            candidate = _make_generated_rule_id(prefix, f"{fallback_seed}:{len(seen_ids)}")
    seen_ids.add(candidate)
    return candidate


def _build_whitelist_targets_from_model_ids(
    model_ids: list[int],
    existing_targets: object = None,
    *,
    default_keep_count: int = 0,
) -> list[WhitelistTarget]:
    target_settings_by_model = {
        int(target.model_id): (
            max(0, int(target.keep_count)),
            bool(getattr(target, "deposit_to_storage", False)),
        )
        for target in _normalize_whitelist_targets(existing_targets)
    }
    safe_default_keep_count = max(0, _safe_int(default_keep_count, 0))
    return [
        WhitelistTarget(
            model_id=model_id,
            keep_count=target_settings_by_model.get(model_id, (safe_default_keep_count, False))[0],
            deposit_to_storage=target_settings_by_model.get(model_id, (safe_default_keep_count, False))[1],
        )
        for model_id in _dedupe_model_ids(model_ids)
    ]


def _merge_whitelist_targets_with_legacy_model_ids(
    legacy_model_ids: list[int],
    existing_targets: object = None,
    *,
    default_keep_count: int = 0,
) -> list[WhitelistTarget]:
    normalized_targets = _normalize_whitelist_targets(existing_targets)
    merged_targets = [
        WhitelistTarget(
            model_id=int(target.model_id),
            keep_count=max(0, int(target.keep_count)),
            deposit_to_storage=bool(getattr(target, "deposit_to_storage", False)),
        )
        for target in normalized_targets
    ]
    existing_model_ids = {int(target.model_id) for target in merged_targets}
    safe_default_keep_count = max(0, _safe_int(default_keep_count, 0))
    for model_id in _dedupe_model_ids(legacy_model_ids):
        if model_id in existing_model_ids:
            continue
        merged_targets.append(
            WhitelistTarget(
                model_id=model_id,
                keep_count=safe_default_keep_count,
                deposit_to_storage=False,
            )
        )
    return merged_targets


def _get_whitelist_target_model_ids(raw_targets: object) -> list[int]:
    return [
        int(target.model_id)
        for target in _normalize_whitelist_targets(raw_targets)
    ]


def _normalize_weapon_requirement_rules(raw_rules: object) -> list[WeaponRequirementRule]:
    normalized: list[WeaponRequirementRule] = []
    seen_model_ids: set[int] = set()
    if not isinstance(raw_rules, list):
        return normalized

    for entry in raw_rules:
        if isinstance(entry, WeaponRequirementRule):
            model_id = entry.model_id
            min_requirement = getattr(entry, "min_requirement", 0)
            max_requirement = entry.max_requirement
        elif isinstance(entry, dict):
            model_id = entry.get("model_id", 0)
            max_requirement = entry.get("max_requirement", 0)
            min_requirement = entry.get(
                "min_requirement",
                1 if _normalize_weapon_requirement_level(max_requirement) > 0 else 0,
            )
        else:
            continue

        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0 or safe_model_id in seen_model_ids:
            continue

        min_requirement, max_requirement = _normalize_weapon_requirement_range(min_requirement, max_requirement)
        seen_model_ids.add(safe_model_id)
        normalized.append(
            WeaponRequirementRule(
                model_id=safe_model_id,
                min_requirement=min_requirement,
                max_requirement=max_requirement,
            )
        )

    return normalized


def _get_buy_rule_merchant_type(rule: BuyRule) -> str:
    if rule.kind == BUY_KIND_MATERIAL_TARGET:
        return MERCHANT_TYPE_MATERIALS
    if rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
        return MERCHANT_TYPE_RUNE_TRADER
    return BUY_KIND_TO_MERCHANT_TYPE.get(rule.kind, MERCHANT_TYPE_MERCHANT)


def _default_buy_rules() -> list[BuyRule]:
    return [
        BuyRule(enabled=False, kind=BUY_KIND_MERCHANT_STOCK, merchant_type=MERCHANT_TYPE_MERCHANT, model_id=0, target_count=0, max_per_run=0),
        BuyRule(enabled=False, kind=BUY_KIND_MATERIAL_TARGET, merchant_type=MERCHANT_TYPE_MATERIALS, model_id=0, target_count=0, max_per_run=0),
        BuyRule(enabled=False, kind=BUY_KIND_RUNE_TRADER_TARGET, merchant_type=MERCHANT_TYPE_RUNE_TRADER, model_id=0, target_count=0, max_per_run=0),
    ]


def _default_sell_rules() -> list[SellRule]:
    return [
        SellRule(enabled=False, kind=SELL_KIND_COMMON_MATERIALS, merchant_type=MERCHANT_TYPE_MATERIALS, model_ids=[], keep_count=0),
        SellRule(enabled=False, kind=SELL_KIND_EXPLICIT_MODELS, merchant_type=MERCHANT_TYPE_MERCHANT, model_ids=[], keep_count=0),
        SellRule(
            enabled=False,
            kind=SELL_KIND_WEAPONS,
            merchant_type=MERCHANT_TYPE_MERCHANT,
            rarities=_default_rarity_flags(),
            skip_customized=True,
            skip_unidentified=True,
        ),
        SellRule(
            enabled=False,
            kind=SELL_KIND_ARMOR,
            merchant_type=MERCHANT_TYPE_MERCHANT,
            rarities=_default_rarity_flags(),
            skip_customized=True,
            skip_unidentified=True,
        ),
    ]


def _default_destroy_rules() -> list[DestroyRule]:
    return [
        DestroyRule(enabled=False, kind=DESTROY_KIND_WEAPONS, rarities=_default_rarity_flags()),
        DestroyRule(enabled=False, kind=DESTROY_KIND_ARMOR, rarities=_default_rarity_flags()),
        DestroyRule(enabled=False, kind=DESTROY_KIND_EXPLICIT_MODELS, model_ids=[], keep_count=0),
        DestroyRule(enabled=False, kind=DESTROY_KIND_MATERIALS, model_ids=[], keep_count=0),
    ]


def _normalize_buy_rule(rule: BuyRule) -> BuyRule | None:
    legacy_model_id = max(0, _safe_int(rule.model_id, 0))
    legacy_target_count = max(0, _safe_int(rule.target_count, 0))
    legacy_max_per_run = max(0, _safe_int(rule.max_per_run, 0))

    if rule.kind == LEGACY_BUY_KIND_ID_KITS:
        return None
    if rule.kind == LEGACY_BUY_KIND_SALVAGE_KITS:
        rule.kind = BUY_KIND_MERCHANT_STOCK
        legacy_model_id = SALVAGE_KIT_MODEL_ID
    elif rule.kind == LEGACY_BUY_KIND_ECTO:
        rule.kind = BUY_KIND_MATERIAL_TARGET
        legacy_model_id = ECTOPLASM_MODEL_ID
    if rule.kind not in BUY_RULE_KINDS:
        rule.kind = BUY_KIND_MERCHANT_STOCK

    rule.model_id = legacy_model_id
    rule.target_count = legacy_target_count
    rule.max_per_run = legacy_max_per_run
    rule.merchant_stock_targets = _normalize_merchant_stock_targets(getattr(rule, "merchant_stock_targets", []))
    rule.material_targets = _normalize_material_targets(getattr(rule, "material_targets", []))
    rule.rune_targets = _normalize_rune_trader_targets(getattr(rule, "rune_targets", []))

    if rule.kind == BUY_KIND_MATERIAL_TARGET:
        if not rule.material_targets and legacy_model_id > 0 and _is_crafting_material_model(legacy_model_id):
            rule.material_targets = [
                MaterialTarget(
                    model_id=legacy_model_id,
                    target_count=legacy_target_count,
                    max_per_run=legacy_max_per_run,
                )
            ]
        rule.merchant_stock_targets = []
        rule.rune_targets = []
        rule.model_id = 0
        rule.target_count = 0
        rule.max_per_run = 0
    elif rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
        rule.merchant_stock_targets = []
        rule.material_targets = []
        rule.model_id = 0
        rule.target_count = 0
        rule.max_per_run = 0
    else:
        if not rule.merchant_stock_targets and legacy_model_id > 0:
            rule.merchant_stock_targets = [
                MerchantStockTarget(
                    model_id=legacy_model_id,
                    target_count=legacy_target_count,
                    max_per_run=legacy_max_per_run,
                )
            ]
        rule.material_targets = []
        rule.rune_targets = []
        rule.model_id = 0
        rule.target_count = 0
        rule.max_per_run = 0

    rule.name = _normalize_rule_name(getattr(rule, "name", ""))
    rule.merchant_type = _get_buy_rule_merchant_type(rule)
    return rule


def _normalize_buy_rules(rules: list[BuyRule]) -> list[BuyRule]:
    normalized_rules: list[BuyRule] = []
    for rule in rules:
        normalized = _normalize_buy_rule(rule)
        if normalized is not None:
            normalized_rules.append(normalized)
    return normalized_rules


def _make_model_stock_key(model_id: object) -> str:
    safe_model_id = max(0, _safe_int(model_id, 0))
    return f"{STOCK_KEY_MODEL_PREFIX}{safe_model_id}" if safe_model_id > 0 else ""


def _make_identifier_stock_key(identifier: object) -> str:
    safe_identifier = _normalize_rune_identifier(identifier)
    return f"{STOCK_KEY_IDENTIFIER_PREFIX}{safe_identifier}" if safe_identifier else ""


def _parse_stock_key(key: object) -> tuple[str, str]:
    safe_key = str(key or "").strip()
    if safe_key.startswith(STOCK_KEY_MODEL_PREFIX):
        return STOCK_KEY_MODEL_PREFIX, safe_key[len(STOCK_KEY_MODEL_PREFIX):]
    if safe_key.startswith(STOCK_KEY_IDENTIFIER_PREFIX):
        return STOCK_KEY_IDENTIFIER_PREFIX, safe_key[len(STOCK_KEY_IDENTIFIER_PREFIX):]
    return "", safe_key


def _normalize_rune_catalog_profession(value: object) -> str:
    safe_value = str(value or "").strip()
    return safe_value or "_None"


def _get_rune_profession_label(value: object) -> str:
    profession = _normalize_rune_catalog_profession(value)
    return "Common" if profession == "_None" else profession


def _get_rune_kind_label(mod_type: object) -> str:
    return "Insignia" if str(mod_type or "").strip().lower() == "prefix" else "Rune"


def _get_rune_kind_sort_key(mod_type: object) -> int:
    return 0 if _get_rune_kind_label(mod_type) == "Insignia" else 1


def _get_rune_rarity_sort_key(rarity: object) -> int:
    rarity_order = {"blue": 0, "purple": 1, "gold": 2}
    return rarity_order.get(str(rarity or "").strip().lower(), 99)


def _normalize_sell_rule(rule: SellRule) -> SellRule | None:
    legacy_model_ids = _dedupe_model_ids(getattr(rule, "model_ids", []))
    legacy_keep_count = max(0, int(getattr(rule, "keep_count", 0)))
    if rule.kind == LEGACY_SELL_KIND_WEAPONS_BY_RARITY:
        rule.kind = SELL_KIND_WEAPONS
    elif rule.kind == LEGACY_SELL_KIND_ARMOR_BY_RARITY:
        rule.kind = SELL_KIND_ARMOR
    elif rule.kind == LEGACY_SELL_KIND_NONSALVAGEABLE_GOLDS:
        return None
    if rule.kind not in SELL_RULE_KINDS:
        rule.kind = SELL_KIND_EXPLICIT_MODELS
    rule.merchant_type = SELL_KIND_TO_MERCHANT_TYPE[rule.kind]
    rule.rule_id = _normalize_rule_id(getattr(rule, "rule_id", ""))
    rule.keep_count = legacy_keep_count
    rule.model_ids = legacy_model_ids
    rule.whitelist_targets = _merge_whitelist_targets_with_legacy_model_ids(
        legacy_model_ids,
        getattr(rule, "whitelist_targets", []),
        default_keep_count=legacy_keep_count,
    )
    rule.rarities = _normalize_rarity_flags(rule.rarities)
    rule.blacklist_model_ids = _dedupe_model_ids(rule.blacklist_model_ids)
    rule.blacklist_item_type_ids = _dedupe_weapon_item_type_ids(rule.blacklist_item_type_ids)
    (
        rule.all_weapons_min_requirement,
        rule.all_weapons_max_requirement,
    ) = _normalize_weapon_requirement_range(
        getattr(rule, "all_weapons_min_requirement", 0),
        getattr(rule, "all_weapons_max_requirement", 0),
    )
    rule.protected_weapon_requirement_rules = _normalize_weapon_requirement_rules(getattr(rule, "protected_weapon_requirement_rules", []))
    rule.protected_weapon_mod_identifiers = _dedupe_identifiers(rule.protected_weapon_mod_identifiers)
    rule.protected_rune_identifiers = _dedupe_identifiers(rule.protected_rune_identifiers)
    rule.skip_customized = bool(rule.skip_customized)
    rule.skip_unidentified = bool(rule.skip_unidentified)
    rule.include_standalone_runes = bool(rule.include_standalone_runes)
    rule.deposit_protected_matches = bool(getattr(rule, "deposit_protected_matches", False))
    rule.name = _normalize_rule_name(getattr(rule, "name", ""))
    rule.whitelist_targets = _normalize_whitelist_targets(rule.whitelist_targets)
    if rule.kind in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
        rule.model_ids = []
        rule.keep_count = 0
        rule.whitelist_targets = []
        if rule.kind != SELL_KIND_WEAPONS:
            rule.blacklist_item_type_ids = []
    else:
        rule.model_ids = _get_whitelist_target_model_ids(rule.whitelist_targets)
        rule.keep_count = 0
        rule.blacklist_item_type_ids = []
        rule.deposit_protected_matches = False
    return rule


def _normalize_sell_rules(rules: list[SellRule]) -> list[SellRule]:
    normalized_rules: list[SellRule] = []
    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        normalized = _normalize_sell_rule(rule)
        if normalized is not None:
            normalized.rule_id = _ensure_unique_rule_id(
                normalized.rule_id,
                seen_ids=seen_rule_ids,
                prefix="sell",
                fallback_seed=f"{index}:{normalized.kind}:{normalized.name}",
            )
            normalized_rules.append(normalized)
    return normalized_rules


def _normalize_destroy_rule(rule: DestroyRule) -> DestroyRule:
    legacy_model_ids = _dedupe_model_ids(getattr(rule, "model_ids", []))
    legacy_keep_count = max(0, int(getattr(rule, "keep_count", 0)))
    if rule.kind not in DESTROY_RULE_KINDS:
        rule.kind = DESTROY_KIND_EXPLICIT_MODELS
    rule.keep_count = legacy_keep_count
    rule.model_ids = legacy_model_ids
    rule.whitelist_targets = _merge_whitelist_targets_with_legacy_model_ids(
        legacy_model_ids,
        getattr(rule, "whitelist_targets", []),
        default_keep_count=legacy_keep_count,
    )
    rule.rarities = _normalize_rarity_flags(getattr(rule, "rarities", {}))
    rule.name = _normalize_rule_name(getattr(rule, "name", ""))
    if rule.kind in (DESTROY_KIND_WEAPONS, DESTROY_KIND_ARMOR):
        rule.model_ids = []
        rule.keep_count = 0
        rule.whitelist_targets = []
    else:
        rule.model_ids = _get_whitelist_target_model_ids(rule.whitelist_targets)
        rule.keep_count = 0
    return rule


def _normalize_destroy_rules(rules: list[DestroyRule]) -> list[DestroyRule]:
    return [_normalize_destroy_rule(rule) for rule in rules]


def _serialize_sell_rule(rule: SellRule) -> dict[str, object]:
    normalized_rule = _normalize_sell_rule(rule)
    if normalized_rule is None:
        return {}

    payload = asdict(normalized_rule)
    payload["rule_id"] = str(normalized_rule.rule_id or "").strip()
    payload["whitelist_targets"] = _serialize_whitelist_targets(normalized_rule.whitelist_targets)
    return payload


def _serialize_destroy_rule(rule: DestroyRule) -> dict[str, object]:
    normalized_rule = _normalize_destroy_rule(rule)
    payload = asdict(normalized_rule)
    payload["whitelist_targets"] = _serialize_whitelist_targets(normalized_rule.whitelist_targets)
    return payload


def _has_explicit_equippable_hard_protection(rule: SellRule) -> bool:
    if rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
        return False
    if rule.blacklist_model_ids:
        return True
    if rule.kind == SELL_KIND_WEAPONS:
        return bool(
            rule.blacklist_item_type_ids
            or _is_weapon_requirement_range_active(
                getattr(rule, "all_weapons_min_requirement", 0),
                getattr(rule, "all_weapons_max_requirement", 0),
            )
            or any(
                _is_weapon_requirement_range_active(
                    getattr(requirement_rule, "min_requirement", 0),
                    getattr(requirement_rule, "max_requirement", 0),
                )
                for requirement_rule in rule.protected_weapon_requirement_rules
            )
            or rule.protected_weapon_mod_identifiers
        )
    return bool(rule.protected_rune_identifiers)


class MerchantRulesWidget:
    def __init__(self):
        self.initialized = False
        self.legacy_recovery_artifacts_migrated = False
        self.account_key = ""
        self.config_path = ""
        self.new_profile_session = False
        self.profile_warning = ""
        self.profile_notice = ""
        self.shared_profile_entries: list[SharedProfileSummary] = []
        self.shared_profile_selected_path = ""
        self.shared_profile_name_input = ""
        self.shared_profile_warning = ""
        self.shared_profile_notice = ""
        self.shared_profile_scan_warning = ""
        self.shared_profile_entries_loaded = False
        self.shared_profile_pending_overwrite_path = ""
        self.shared_profile_pending_delete_path = ""
        self.buy_rules: list[BuyRule] = []
        self.sell_rules: list[SellRule] = []
        self.destroy_rules: list[DestroyRule] = []
        self.cleanup_targets: list[CleanupTarget] = []
        self.cleanup_protection_sources: list[CleanupProtectionSource] = []
        self.auto_cleanup_on_outpost_entry = False
        self.auto_travel_enabled = False
        self.target_outpost_id = 0
        self.favorite_outpost_ids: list[int] = []
        self.preview_plan = PlanResult()
        self.preview_ready = False
        self.preview_requires_execute_travel = False
        self.preview_execute_travel_target_outpost_id = 0
        self.preview_execute_travel_target_outpost_name = ""
        self.execution_running = False
        self.travel_preview_running = False
        self.instant_destroy_running = False
        self.auto_cleanup_running = False
        self.destroy_instant_enabled = False
        self.destroy_include_protected_items = False
        self.status_message = "Preview the current map plan before execution."
        self.last_error = ""
        self.last_execution_summary = ""
        self.last_instant_destroy_summary = ""
        self.last_cleanup_summary = ""
        self.debug_logging = False
        self.storage_scan_running = False
        self.outpost_search_text = ""
        self.cleanup_model_search_text = ""
        self.destroy_model_text_cache: dict[int, str] = {}
        self.destroy_model_search_cache: dict[int, str] = {}
        self.sell_model_text_cache: dict[int, str] = {}
        self.buy_model_search_cache: dict[int, str] = {}
        self.buy_manual_model_id_cache: dict[int, int] = {}
        self.buy_rune_search_cache: dict[int, str] = {}
        self.buy_rune_profession_cache: dict[int, str] = {}
        self.sell_model_search_cache: dict[int, str] = {}
        self.sell_blacklist_search_cache: dict[int, str] = {}
        self.sell_blacklist_import_feedback_cache: dict[int, tuple[str, tuple[float, float, float, float]]] = {}
        self.sell_weapon_requirement_search_cache: dict[int, str] = {}
        self.sell_weapon_mod_search_cache: dict[int, str] = {}
        self.sell_rune_search_cache: dict[int, str] = {}
        self.map_snapshot = 0
        self.map_ready_snapshot = False
        self.map_instance_uptime_snapshot_ms = 0
        self.auto_cleanup_zone_attempted = False
        self.auto_cleanup_zone_token = ""
        self.inventory_modifier_cache: dict[int, InventoryModifierCacheEntry] = {}
        self.inventory_modifier_cache_hits = 0
        self.inventory_modifier_cache_misses = 0
        self.last_inventory_snapshot_duration_ms = 0.0
        self.last_plan_build_duration_ms = 0.0
        self.last_preview_compare_duration_ms = 0.0
        self.last_execution_phase_durations_ms: dict[str, float] = {}
        self.preview_inventory_diff_summary = ""
        self.preview_inventory_diff_rows: list[str] = []
        self.execute_drift_requires_confirmation = False
        self.cached_context_map_id = -1
        self.cached_supported_context: tuple[bool, str, dict[str, tuple[float, float] | None]] | None = None
        self.catalog_loaded = False
        self.catalog_load_error = ""
        self.catalog_by_model_id: dict[int, dict[str, object]] = {}
        self.catalog_alias_to_model_ids: dict[str, list[int]] = {}
        self.catalog_alias_display_names: dict[str, str] = {}
        self.catalog_common_material_ids: list[int] = []
        self.catalog_merchant_essentials: list[dict[str, object]] = []
        self.catalog_rare_materials: list[dict[str, object]] = []
        self.catalog_stats: dict[str, int | bool] = {}
        self.weapon_mod_entries: list[dict[str, str]] = []
        self.rune_entries: list[dict[str, str]] = []
        self.weapon_mod_names: dict[str, str] = {}
        self.rune_names: dict[str, str] = {}
        self.rune_buy_entries: list[dict[str, object]] = []
        self.rune_buy_entries_by_identifier: dict[str, dict[str, object]] = {}
        self.rune_buy_entries_by_profession: dict[str, list[dict[str, object]]] = {}
        self.rune_buy_professions: list[str] = []
        self.outpost_entries: list[dict[str, object]] = []
        self.window_x: int | None = None
        self.window_y: int | None = None
        self.window_width = 0
        self.window_height = 0
        self.window_collapsed = False
        self.window_geometry_needs_apply = True
        self.window_geometry_dirty = False
        self.window_geometry_save_timer = ThrottledTimer(WINDOW_GEOMETRY_SAVE_THROTTLE_MS)
        self.instant_destroy_poll_timer = ThrottledTimer(INSTANT_DESTROY_POLL_MS)
        self.instant_destroy_rescan_requested = False
        self.instant_destroy_last_signature: tuple[tuple[int, int], ...] = ()
        self.active_workspace = WORKSPACE_OVERVIEW
        self.active_rules_workspace = RULES_WORKSPACE_BUY
        self.active_buy_rule_kind = BUY_RULE_WORKSPACE_ORDER[0]
        self.active_sell_rule_kind = SELL_RULE_WORKSPACE_ORDER[0]
        self.active_destroy_rule_kind = DESTROY_RULE_WORKSPACE_ORDER[0]
        self.protections_search_text = ""
        self.protections_owner_filter = PROTECTION_FILTER_ALL
        self.protections_type_filter = PROTECTION_FILTER_ALL
        self.protections_active_only = False
        self.sell_protection_jump_target: SellProtectionJumpTarget | None = None
        self.rule_ui_structure_changed = False
        self.multibox_selected_accounts: dict[str, bool] = {}
        self.multibox_statuses: dict[str, MultiboxAccountStatus] = {}
        self.multibox_active_request_id = ""
        self.multibox_active_action = ""
        self.multibox_pending_accounts: list[str] = []
        self.multibox_running_email = ""
        self.multibox_running_started_at_ms = 0
        self.show_main_window = False
        self.expand_main_window_on_next_show = True
        self.floating_ui_ini_key = ""
        self.floating_ui_ini_loaded = False
        self.floating_button = None
        self.multibox_running_accounts: dict[str, int] = {}
        self.multibox_request_counter = 0

    def _get_account_key(self) -> str:
        account_email = str(Player.GetAccountEmail() or "").strip()
        if account_email:
            return account_email
        character_name = str(Player.GetName() or "").strip()
        if character_name:
            return character_name
        return "default"

    def _get_config_filename_for_account(self, account_key: str) -> str:
        return _get_config_filename_for_account_key(account_key)

    def _get_config_path_for_account(self, account_key: str) -> str:
        return _get_config_path_for_account_key(account_key)

    def _get_floating_icon_path(self) -> str:
        return os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON)

    def _ensure_floating_ui_key(self) -> str:
        if self.floating_ui_ini_key:
            return self.floating_ui_ini_key
        try:
            from Py4GWCoreLib.IniManager import IniManager
        except Exception:
            return ""
        self.floating_ui_ini_key = IniManager().ensure_key(
            FLOATING_UI_INI_PATH,
            FLOATING_UI_INI_FILENAME,
        )
        return self.floating_ui_ini_key

    def _ensure_floating_ui(self):
        if self.floating_button is None:
            from Py4GWCoreLib.ImGui import ImGui

            self.floating_button = ImGui.FloatingIcon(
                icon_path=self._get_floating_icon_path(),
                window_id=FLOATING_ICON_WINDOW_ID,
                window_name=FLOATING_ICON_WINDOW_NAME,
                tooltip_visible="Hide Merchant Rules window",
                tooltip_hidden="Show Merchant Rules window",
                visible=bool(self.show_main_window),
                on_toggle=self._on_floating_icon_visibility_toggled,
            )

        self.floating_button.set_visible(
            bool(self.show_main_window),
            persist=False,
            invoke_callback=False,
        )

        floating_ui_ini_key = self._ensure_floating_ui_key()
        if floating_ui_ini_key and not self.floating_ui_ini_loaded:
            from Py4GWCoreLib.IniManager import IniManager

            IniManager().load_once(floating_ui_ini_key)
            self.floating_ui_ini_loaded = True

        return self.floating_button

    def _set_main_window_visible(self, visible: bool, *, expand_on_show: bool = True):
        self.show_main_window = bool(visible)
        if self.show_main_window and expand_on_show:
            self.expand_main_window_on_next_show = True
        if self.floating_button is not None:
            self.floating_button.set_visible(
                self.show_main_window,
                persist=False,
                invoke_callback=False,
            )

    def _on_floating_icon_visibility_toggled(self, visible: bool):
        self.show_main_window = bool(visible)
        if self.show_main_window:
            self.expand_main_window_on_next_show = True

    def on_enable(self):
        self._set_main_window_visible(False, expand_on_show=True)

    def _tick_runtime(self):
        self._ensure_initialized()
        self._advance_multibox_batch()
        self._update_auto_cleanup_runtime()
        self._update_instant_destroy_runtime()

    def _draw_main_window(self):
        self._apply_window_geometry()
        if self.expand_main_window_on_next_show:
            PyImGui.set_next_window_collapsed(False, PyImGui.ImGuiCond.Always)
            self.expand_main_window_on_next_show = False

        window_expanded, window_open = PyImGui.begin_with_close(
            MODULE_NAME,
            self.show_main_window,
            PyImGui.WindowFlags.NoFlag,
        )
        self._track_window_geometry(window_expanded)
        self._set_main_window_visible(window_open, expand_on_show=False)
        if not window_expanded or not window_open:
            PyImGui.end()
            return False
        return True

    def _get_default_window_geometry_payload(self) -> dict[str, object]:
        return {
            "window_x": None,
            "window_y": None,
            "window_width": 0,
            "window_height": 0,
            "window_collapsed": False,
        }

    def _build_window_geometry_payload(self) -> dict[str, object]:
        return {
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": max(0, int(self.window_width)),
            "window_height": max(0, int(self.window_height)),
            "window_collapsed": bool(self.window_collapsed),
        }

    def _normalize_window_geometry_payload(self, raw_payload: object) -> dict[str, object]:
        geometry_payload = dict(raw_payload) if isinstance(raw_payload, dict) else {}
        default_payload = self._get_default_window_geometry_payload()
        raw_window_x = geometry_payload.get("window_x", default_payload["window_x"])
        raw_window_y = geometry_payload.get("window_y", default_payload["window_y"])
        return {
            "window_x": _safe_int(raw_window_x, 0) if raw_window_x is not None else None,
            "window_y": _safe_int(raw_window_y, 0) if raw_window_y is not None else None,
            "window_width": max(0, _safe_int(geometry_payload.get("window_width", default_payload["window_width"]), 0)),
            "window_height": max(0, _safe_int(geometry_payload.get("window_height", default_payload["window_height"]), 0)),
            "window_collapsed": bool(geometry_payload.get("window_collapsed", default_payload["window_collapsed"])),
        }

    def _snapshot_window_geometry_state(self) -> dict[str, object]:
        return self._build_window_geometry_payload()

    def _restore_window_geometry_state(self, raw_payload: object) -> bool:
        current_payload = self._snapshot_window_geometry_state()
        normalized_payload = self._normalize_window_geometry_payload(raw_payload)
        self.window_x = normalized_payload["window_x"]
        self.window_y = normalized_payload["window_y"]
        self.window_width = normalized_payload["window_width"]
        self.window_height = normalized_payload["window_height"]
        self.window_collapsed = normalized_payload["window_collapsed"]
        self.window_geometry_needs_apply = True
        return normalized_payload != current_payload

    def _build_profile_payload(self, *, include_window_geometry: bool = True) -> dict[str, object]:
        payload = {
            "version": PROFILE_VERSION,
            "auto_cleanup_on_outpost_entry": bool(self.auto_cleanup_on_outpost_entry),
            "auto_travel_enabled": bool(self.auto_travel_enabled),
            "target_outpost_id": max(0, int(self.target_outpost_id)),
            "favorite_outpost_ids": self._normalize_outpost_ids(self.favorite_outpost_ids),
            "debug_logging": bool(self.debug_logging),
            "buy_rules": [asdict(rule) for rule in _normalize_buy_rules(self.buy_rules)],
            "sell_rules": [
                payload_entry
                for payload_entry in (_serialize_sell_rule(rule) for rule in _normalize_sell_rules(self.sell_rules))
                if payload_entry
            ],
            "destroy_rules": [_serialize_destroy_rule(rule) for rule in _normalize_destroy_rules(self.destroy_rules)],
            "cleanup_targets": _serialize_cleanup_targets(self.cleanup_targets),
            "cleanup_protection_sources": _serialize_cleanup_protection_sources(self.cleanup_protection_sources),
        }
        if include_window_geometry:
            payload.update(self._build_window_geometry_payload())
        return payload

    def _serialize_profile_payload(self, payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def _normalize_profile_payload(self, raw_payload: object) -> dict[str, object]:
        if not isinstance(raw_payload, dict):
            raise ValueError("Merchant Rules profile must be a JSON object.")

        buy_rules_raw = raw_payload.get("buy_rules", [asdict(rule) for rule in _default_buy_rules()])
        if not isinstance(buy_rules_raw, list):
            raise ValueError("Merchant Rules buy_rules must be a list.")

        sell_rules_raw = raw_payload.get("sell_rules", [asdict(rule) for rule in _default_sell_rules()])
        if not isinstance(sell_rules_raw, list):
            raise ValueError("Merchant Rules sell_rules must be a list.")

        destroy_rules_raw = raw_payload.get("destroy_rules", [asdict(rule) for rule in _default_destroy_rules()])
        if not isinstance(destroy_rules_raw, list):
            raise ValueError("Merchant Rules destroy_rules must be a list.")

        cleanup_targets_present = "cleanup_targets" in raw_payload
        cleanup_targets_raw = raw_payload.get("cleanup_targets", [])
        if cleanup_targets_raw is None:
            cleanup_targets_raw = []
        if not isinstance(cleanup_targets_raw, list):
            raise ValueError("Merchant Rules cleanup_targets must be a list.")

        cleanup_sources_present = "cleanup_protection_sources" in raw_payload
        cleanup_sources_raw = raw_payload.get("cleanup_protection_sources", [])
        if cleanup_sources_raw is None:
            cleanup_sources_raw = []
        if not isinstance(cleanup_sources_raw, list):
            raise ValueError("Merchant Rules cleanup_protection_sources must be a list.")

        favorite_outpost_ids_raw = raw_payload.get("favorite_outpost_ids", [])
        if favorite_outpost_ids_raw is None:
            favorite_outpost_ids_raw = []
        if not isinstance(favorite_outpost_ids_raw, list):
            raise ValueError("Merchant Rules favorite_outpost_ids must be a list.")

        normalized_buy_rules: list[BuyRule] = []
        for entry in buy_rules_raw:
            if not isinstance(entry, dict):
                raise ValueError("Merchant Rules buy rule entries must be objects.")
            rule = BuyRule(
                enabled=bool(entry.get("enabled", False)),
                kind=str(entry.get("kind", BUY_KIND_MERCHANT_STOCK)),
                merchant_type=str(entry.get("merchant_type", MERCHANT_TYPE_MERCHANT)),
                model_id=_safe_int(entry.get("model_id", 0), 0),
                target_count=_safe_int(entry.get("target_count", 0), 0),
                max_per_run=_safe_int(entry.get("max_per_run", 0), 0),
                merchant_stock_targets=_normalize_merchant_stock_targets(_coerce_list(entry.get("merchant_stock_targets", []))),
                material_targets=_normalize_material_targets(_coerce_list(entry.get("material_targets", []))),
                rune_targets=_normalize_rune_trader_targets(_coerce_list(entry.get("rune_targets", []))),
                name=_normalize_rule_name(entry.get("name", "")),
            )
            normalized_buy_rule = _normalize_buy_rule(rule)
            if normalized_buy_rule is not None:
                normalized_buy_rules.append(normalized_buy_rule)

        normalized_sell_rules: list[SellRule] = []
        migrated_cleanup_targets_by_model: dict[int, CleanupTarget] = {}
        migrated_cleanup_sources: list[CleanupProtectionSource] = []
        seen_sell_rule_ids: set[str] = set()
        for entry in sell_rules_raw:
            if not isinstance(entry, dict):
                raise ValueError("Merchant Rules sell rule entries must be objects.")
            raw_whitelist_targets = _normalize_whitelist_targets(_coerce_list(entry.get("whitelist_targets", [])))
            normalized_rule = _normalize_sell_rule(
                SellRule(
                    enabled=bool(entry.get("enabled", False)),
                    kind=str(entry.get("kind", SELL_KIND_EXPLICIT_MODELS)),
                    merchant_type=str(entry.get("merchant_type", MERCHANT_TYPE_MERCHANT)),
                    rule_id=_normalize_rule_id(entry.get("rule_id", "")),
                    model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("model_ids", []))],
                    keep_count=_safe_int(entry.get("keep_count", 0), 0),
                    whitelist_targets=raw_whitelist_targets,
                    rarities=_normalize_rarity_flags(entry.get("rarities", {})),
                    blacklist_model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("blacklist_model_ids", []))],
                    blacklist_item_type_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("blacklist_item_type_ids", []))],
                    all_weapons_min_requirement=_normalize_all_weapons_requirement_range_from_payload(entry)[0],
                    all_weapons_max_requirement=_normalize_all_weapons_requirement_range_from_payload(entry)[1],
                    protected_weapon_requirement_rules=_normalize_weapon_requirement_rules(_coerce_list(entry.get("protected_weapon_requirement_rules", []))),
                    protected_weapon_mod_identifiers=_dedupe_identifiers(_coerce_list(entry.get("protected_weapon_mod_identifiers", []))),
                    protected_rune_identifiers=_dedupe_identifiers(_coerce_list(entry.get("protected_rune_identifiers", []))),
                    skip_customized=bool(entry.get("skip_customized", True)),
                    skip_unidentified=bool(entry.get("skip_unidentified", True)),
                    include_standalone_runes=bool(entry.get("include_standalone_runes", False)),
                    deposit_protected_matches=bool(entry.get("deposit_protected_matches", False)),
                    name=_normalize_rule_name(entry.get("name", "")),
                )
            )
            if normalized_rule is None:
                continue
            normalized_rule.rule_id = _ensure_unique_rule_id(
                normalized_rule.rule_id,
                seen_ids=seen_sell_rule_ids,
                prefix="sell",
                fallback_seed=f"{len(normalized_sell_rules)}:{normalized_rule.kind}:{normalized_rule.name}",
            )
            normalized_sell_rules.append(normalized_rule)

            if not cleanup_targets_present:
                for whitelist_target in raw_whitelist_targets:
                    if not bool(getattr(whitelist_target, "deposit_to_storage", False)):
                        continue
                    safe_model_id = max(0, int(whitelist_target.model_id))
                    if safe_model_id <= 0:
                        continue
                    existing_target = migrated_cleanup_targets_by_model.get(safe_model_id)
                    keep_on_character = 0
                    if existing_target is None or keep_on_character > existing_target.keep_on_character:
                        migrated_cleanup_targets_by_model[safe_model_id] = CleanupTarget(
                            model_id=safe_model_id,
                            keep_on_character=keep_on_character,
                        )

            if (
                not cleanup_sources_present
                and normalized_rule.kind in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR)
                and bool(entry.get("deposit_protected_matches", False))
            ):
                migrated_cleanup_sources.append(
                    CleanupProtectionSource(sell_rule_id=normalized_rule.rule_id)
                )

        destroy_rules_to_normalize: list[DestroyRule] = []
        for entry in destroy_rules_raw:
            if not isinstance(entry, dict):
                raise ValueError("Merchant Rules destroy rule entries must be objects.")
            destroy_rules_to_normalize.append(
                DestroyRule(
                    enabled=bool(entry.get("enabled", False)),
                    kind=str(entry.get("kind", DESTROY_KIND_EXPLICIT_MODELS)),
                    model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("model_ids", []))],
                    keep_count=_safe_int(entry.get("keep_count", 0), 0),
                    whitelist_targets=_normalize_whitelist_targets(_coerce_list(entry.get("whitelist_targets", []))),
                    rarities=_normalize_rarity_flags(entry.get("rarities", {})),
                    name=_normalize_rule_name(entry.get("name", "")),
                )
            )
        normalized_destroy_rules = _normalize_destroy_rules(destroy_rules_to_normalize)
        normalized_cleanup_targets = _normalize_cleanup_targets(cleanup_targets_raw)
        if not cleanup_targets_present:
            normalized_cleanup_targets = _normalize_cleanup_targets(
                [asdict(target) for target in migrated_cleanup_targets_by_model.values()]
            )

        normalized_cleanup_sources = _normalize_cleanup_protection_sources(cleanup_sources_raw)
        if not cleanup_sources_present:
            normalized_cleanup_sources = _normalize_cleanup_protection_sources(
                [asdict(source) for source in migrated_cleanup_sources]
            )

        window_geometry = self._normalize_window_geometry_payload(raw_payload)
        return {
            "version": PROFILE_VERSION,
            "auto_cleanup_on_outpost_entry": bool(raw_payload.get("auto_cleanup_on_outpost_entry", False)),
            "auto_travel_enabled": bool(raw_payload.get("auto_travel_enabled", False)),
            "target_outpost_id": max(0, _safe_int(raw_payload.get("target_outpost_id", 0), 0)),
            "favorite_outpost_ids": self._normalize_outpost_ids(_coerce_list(favorite_outpost_ids_raw)),
            "debug_logging": bool(raw_payload.get("debug_logging", False)),
            **window_geometry,
            "buy_rules": [asdict(rule) for rule in normalized_buy_rules],
            "sell_rules": [_serialize_sell_rule(rule) for rule in normalized_sell_rules],
            "destroy_rules": [_serialize_destroy_rule(rule) for rule in normalized_destroy_rules],
            "cleanup_targets": _serialize_cleanup_targets(normalized_cleanup_targets),
            "cleanup_protection_sources": _serialize_cleanup_protection_sources(normalized_cleanup_sources),
        }

    def _apply_profile_payload(self, payload: dict[str, object]):
        self.buy_rules = [
            BuyRule(
                enabled=bool(entry.get("enabled", False)),
                kind=str(entry.get("kind", BUY_KIND_MERCHANT_STOCK)),
                merchant_type=str(entry.get("merchant_type", MERCHANT_TYPE_MERCHANT)),
                model_id=_safe_int(entry.get("model_id", 0), 0),
                target_count=_safe_int(entry.get("target_count", 0), 0),
                max_per_run=_safe_int(entry.get("max_per_run", 0), 0),
                merchant_stock_targets=_normalize_merchant_stock_targets(_coerce_list(entry.get("merchant_stock_targets", []))),
                material_targets=_normalize_material_targets(_coerce_list(entry.get("material_targets", []))),
                rune_targets=_normalize_rune_trader_targets(_coerce_list(entry.get("rune_targets", []))),
                name=_normalize_rule_name(entry.get("name", "")),
            )
            for entry in _coerce_list(payload.get("buy_rules", []))
            if isinstance(entry, dict)
        ]
        self.sell_rules = _normalize_sell_rules([
            SellRule(
                enabled=bool(entry.get("enabled", False)),
                kind=str(entry.get("kind", SELL_KIND_EXPLICIT_MODELS)),
                merchant_type=str(entry.get("merchant_type", MERCHANT_TYPE_MERCHANT)),
                rule_id=_normalize_rule_id(entry.get("rule_id", "")),
                model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("model_ids", []))],
                keep_count=_safe_int(entry.get("keep_count", 0), 0),
                whitelist_targets=_normalize_whitelist_targets(_coerce_list(entry.get("whitelist_targets", []))),
                rarities=_normalize_rarity_flags(entry.get("rarities", {})),
                blacklist_model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("blacklist_model_ids", []))],
                blacklist_item_type_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("blacklist_item_type_ids", []))],
                all_weapons_min_requirement=_normalize_all_weapons_requirement_range_from_payload(entry)[0],
                all_weapons_max_requirement=_normalize_all_weapons_requirement_range_from_payload(entry)[1],
                protected_weapon_requirement_rules=_normalize_weapon_requirement_rules(_coerce_list(entry.get("protected_weapon_requirement_rules", []))),
                protected_weapon_mod_identifiers=_dedupe_identifiers(_coerce_list(entry.get("protected_weapon_mod_identifiers", []))),
                protected_rune_identifiers=_dedupe_identifiers(_coerce_list(entry.get("protected_rune_identifiers", []))),
                skip_customized=bool(entry.get("skip_customized", True)),
                skip_unidentified=bool(entry.get("skip_unidentified", True)),
                include_standalone_runes=bool(entry.get("include_standalone_runes", False)),
                deposit_protected_matches=bool(entry.get("deposit_protected_matches", False)),
                name=_normalize_rule_name(entry.get("name", "")),
            )
            for entry in _coerce_list(payload.get("sell_rules", []))
            if isinstance(entry, dict)
        ])
        self.destroy_rules = _normalize_destroy_rules([
            DestroyRule(
                enabled=bool(entry.get("enabled", False)),
                kind=str(entry.get("kind", DESTROY_KIND_EXPLICIT_MODELS)),
                model_ids=[_safe_int(value, 0) for value in _coerce_list(entry.get("model_ids", []))],
                keep_count=_safe_int(entry.get("keep_count", 0), 0),
                whitelist_targets=_normalize_whitelist_targets(_coerce_list(entry.get("whitelist_targets", []))),
                rarities=_normalize_rarity_flags(entry.get("rarities", {})),
                name=_normalize_rule_name(entry.get("name", "")),
            )
            for entry in _coerce_list(payload.get("destroy_rules", []))
            if isinstance(entry, dict)
        ])
        self.cleanup_targets = _normalize_cleanup_targets(_coerce_list(payload.get("cleanup_targets", [])))
        self.cleanup_protection_sources = _normalize_cleanup_protection_sources(
            _coerce_list(payload.get("cleanup_protection_sources", []))
        )
        self.auto_cleanup_on_outpost_entry = bool(payload.get("auto_cleanup_on_outpost_entry", False))
        self.auto_travel_enabled = bool(payload.get("auto_travel_enabled", False))
        self.target_outpost_id = max(0, _safe_int(payload.get("target_outpost_id", 0), 0))
        self.favorite_outpost_ids = self._normalize_outpost_ids(_coerce_list(payload.get("favorite_outpost_ids", [])))
        self.debug_logging = bool(payload.get("debug_logging", False))
        window_geometry = self._normalize_window_geometry_payload(payload)
        self.window_x = window_geometry["window_x"]
        self.window_y = window_geometry["window_y"]
        self.window_width = window_geometry["window_width"]
        self.window_height = window_geometry["window_height"]
        self.window_collapsed = window_geometry["window_collapsed"]
        self.window_geometry_needs_apply = True
        self.window_geometry_dirty = False
        self.window_geometry_save_timer.Reset()
        self.buy_rules = _normalize_buy_rules(self.buy_rules)
        self.sell_rules = _normalize_sell_rules(self.sell_rules)
        self.destroy_rules = _normalize_destroy_rules(self.destroy_rules)
        self.cleanup_targets = _normalize_cleanup_targets(self.cleanup_targets)
        self.cleanup_protection_sources = _normalize_cleanup_protection_sources(self.cleanup_protection_sources)
        self.outpost_search_text = ""
        self.cleanup_model_search_text = ""
        self._refresh_rule_ui_caches()

    def _get_shared_profiles_dir(self) -> str:
        return SHARED_PROFILES_DIR

    def _build_shareable_profile_payload(self) -> dict[str, object]:
        normalized_payload = self._normalize_profile_payload(
            self._build_profile_payload(include_window_geometry=False)
        )
        return _strip_window_geometry_from_profile_payload(normalized_payload)

    def _serialize_shareable_profile_payload(self, payload: dict[str, object]) -> str:
        return self._serialize_profile_payload(
            _strip_window_geometry_from_profile_payload(payload)
        )

    def _format_shared_profile_timestamp(
        self,
        saved_at_unix_ms: int,
        *,
        fallback_path: str = "",
    ) -> str:
        safe_timestamp = max(0, _safe_int(saved_at_unix_ms, 0))
        if safe_timestamp <= 0 and fallback_path and os.path.exists(fallback_path):
            try:
                safe_timestamp = int(os.path.getmtime(fallback_path) * 1000)
            except Exception:
                safe_timestamp = 0
        if safe_timestamp <= 0:
            return ""
        try:
            return time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(float(safe_timestamp) / 1000.0),
            )
        except Exception:
            return ""

    def _build_shared_profile_wrapper(
        self,
        display_name: str,
        *,
        payload: dict[str, object] | None = None,
        saved_at_unix_ms: int | None = None,
    ) -> dict[str, object]:
        normalized_name = _normalize_shared_profile_display_name(display_name)
        if not normalized_name:
            raise ValueError("Enter a profile name before saving.")
        effective_saved_at_unix_ms = (
            max(0, _safe_int(saved_at_unix_ms, 0))
            if saved_at_unix_ms is not None
            else int(time.time() * 1000)
        )
        shareable_payload = (
            self._build_shareable_profile_payload()
            if payload is None
            else _strip_window_geometry_from_profile_payload(
                self._normalize_profile_payload(payload)
            )
        )
        return {
            "schema": SHARED_PROFILE_SCHEMA,
            "schema_version": SHARED_PROFILE_SCHEMA_VERSION,
            "name": normalized_name,
            "saved_at_unix_ms": effective_saved_at_unix_ms,
            "saved_at": self._format_shared_profile_timestamp(
                effective_saved_at_unix_ms
            ),
            "payload": shareable_payload,
        }

    def _normalize_shared_profile_wrapper(
        self,
        raw_payload: object,
        *,
        fallback_name: str = "",
        fallback_path: str = "",
    ) -> dict[str, object]:
        if not isinstance(raw_payload, dict):
            raise ValueError("Shared Merchant Rules profile must be a JSON object.")

        schema = str(raw_payload.get("schema", "") or "").strip()
        if schema == SHARED_PROFILE_SCHEMA:
            raw_schema_version = _safe_int(raw_payload.get("schema_version", 0), 0)
            if raw_schema_version > SHARED_PROFILE_SCHEMA_VERSION:
                raise ValueError(
                    f"Shared profile schema v{raw_schema_version} is newer than supported schema "
                    f"v{SHARED_PROFILE_SCHEMA_VERSION}."
                )
            payload_source = raw_payload.get("payload", {})
            display_name_source = raw_payload.get("name", fallback_name)
        elif _looks_like_merchant_rules_payload(raw_payload):
            payload_source = raw_payload
            display_name_source = fallback_name
        else:
            raise ValueError("Shared Merchant Rules profile schema is not supported.")

        display_name = _normalize_shared_profile_display_name(display_name_source)
        if not display_name:
            raise ValueError("Shared Merchant Rules profile name is missing.")

        payload_version = (
            _safe_int(payload_source.get("version", 0), 0)
            if isinstance(payload_source, dict)
            else 0
        )
        if payload_version > PROFILE_VERSION:
            raise ValueError(
                f"Shared profile payload version {payload_version} is newer than Merchant Rules version "
                f"{PROFILE_VERSION}."
            )

        normalized_payload = _strip_window_geometry_from_profile_payload(
            self._normalize_profile_payload(payload_source)
        )
        saved_at_unix_ms = max(0, _safe_int(raw_payload.get("saved_at_unix_ms", 0), 0))
        saved_at = str(raw_payload.get("saved_at", "") or "").strip()
        if not saved_at:
            saved_at = self._format_shared_profile_timestamp(
                saved_at_unix_ms,
                fallback_path=fallback_path,
            )

        return {
            "schema": SHARED_PROFILE_SCHEMA,
            "schema_version": SHARED_PROFILE_SCHEMA_VERSION,
            "name": display_name,
            "saved_at_unix_ms": saved_at_unix_ms,
            "saved_at": saved_at,
            "payload": normalized_payload,
        }

    def _load_shared_profile_summary_from_path(
        self,
        profile_path: str,
    ) -> SharedProfileSummary:
        with open(profile_path, "r", encoding="utf-8") as file:
            raw_payload = json.load(file)

        fallback_name = os.path.splitext(os.path.basename(profile_path))[0]
        normalized_wrapper = self._normalize_shared_profile_wrapper(
            raw_payload,
            fallback_name=fallback_name,
            fallback_path=profile_path,
        )
        payload = dict(normalized_wrapper.get("payload", {}))
        saved_at_unix_ms = max(
            0,
            _safe_int(normalized_wrapper.get("saved_at_unix_ms", 0), 0),
        )
        if saved_at_unix_ms <= 0 and os.path.exists(profile_path):
            try:
                saved_at_unix_ms = int(os.path.getmtime(profile_path) * 1000)
            except Exception:
                saved_at_unix_ms = 0
        saved_at_label = str(normalized_wrapper.get("saved_at", "") or "").strip()
        if not saved_at_label:
            saved_at_label = self._format_shared_profile_timestamp(
                saved_at_unix_ms,
                fallback_path=profile_path,
            )

        return SharedProfileSummary(
            path=profile_path,
            display_name=str(normalized_wrapper.get("name", "") or fallback_name),
            filename=os.path.basename(profile_path),
            saved_at_label=saved_at_label,
            saved_at_unix_ms=saved_at_unix_ms,
            payload=payload,
            serialized_payload=self._serialize_shareable_profile_payload(payload),
        )

    def _get_selected_shared_profile(self) -> SharedProfileSummary | None:
        selected_path = os.path.normcase(
            os.path.normpath(self.shared_profile_selected_path)
        )
        if not selected_path:
            return None
        for entry in self.shared_profile_entries:
            entry_path = os.path.normcase(os.path.normpath(entry.path))
            if entry_path == selected_path:
                return entry
        return None

    def _clear_shared_profile_confirmation_state(self):
        self.shared_profile_pending_overwrite_path = ""
        self.shared_profile_pending_delete_path = ""

    def _set_selected_shared_profile_path(self, profile_path: str):
        safe_path = str(profile_path or "").strip()
        normalized_current_path = os.path.normcase(
            os.path.normpath(self.shared_profile_selected_path)
        )
        normalized_next_path = os.path.normcase(os.path.normpath(safe_path))
        if normalized_current_path != normalized_next_path:
            self._clear_shared_profile_confirmation_state()
        self.shared_profile_selected_path = safe_path
        selected_profile = self._get_selected_shared_profile()
        if selected_profile is not None:
            self.shared_profile_name_input = str(selected_profile.display_name)
        elif not safe_path:
            self.shared_profile_name_input = ""

    def _find_shared_profile_by_name(
        self,
        display_name: str,
        *,
        exclude_path: str = "",
    ) -> SharedProfileSummary | None:
        normalized_name = _normalize_shared_profile_display_name(display_name).casefold()
        if not normalized_name:
            return None
        normalized_exclude_path = os.path.normcase(os.path.normpath(exclude_path))
        for entry in self.shared_profile_entries:
            entry_path = os.path.normcase(os.path.normpath(entry.path))
            if normalized_exclude_path and entry_path == normalized_exclude_path:
                continue
            if str(entry.display_name).casefold() == normalized_name:
                return entry
        return None

    def _find_shared_profile_by_filename(
        self,
        filename: str,
        *,
        exclude_path: str = "",
    ) -> SharedProfileSummary | None:
        safe_filename = str(filename or "").strip().casefold()
        if not safe_filename:
            return None
        normalized_exclude_path = os.path.normcase(os.path.normpath(exclude_path))
        for entry in self.shared_profile_entries:
            entry_path = os.path.normcase(os.path.normpath(entry.path))
            if normalized_exclude_path and entry_path == normalized_exclude_path:
                continue
            if str(entry.filename).casefold() == safe_filename:
                return entry
        return None

    def _get_shared_profile_path_for_name(self, display_name: str) -> str:
        safe_name = _normalize_shared_profile_display_name(display_name)
        if not safe_name:
            raise ValueError("Enter a profile name before saving.")
        safe_filename = f"{_sanitize_filename(safe_name)}.json"
        return os.path.join(self._get_shared_profiles_dir(), safe_filename)

    def _ensure_shared_profile_name_available(
        self,
        display_name: str,
        *,
        exclude_path: str = "",
    ) -> tuple[str, str]:
        normalized_name = _normalize_shared_profile_display_name(display_name)
        if not normalized_name:
            raise ValueError("Enter a profile name before saving.")

        existing_by_name = self._find_shared_profile_by_name(
            normalized_name,
            exclude_path=exclude_path,
        )
        if existing_by_name is not None:
            raise ValueError(
                f"A shared profile named '{existing_by_name.display_name}' already exists."
            )

        profile_path = self._get_shared_profile_path_for_name(normalized_name)
        existing_by_filename = self._find_shared_profile_by_filename(
            os.path.basename(profile_path),
            exclude_path=exclude_path,
        )
        if existing_by_filename is not None:
            raise ValueError(
                f"Profile name '{normalized_name}' conflicts with existing file "
                f"'{existing_by_filename.display_name}'."
            )
        normalized_profile_path = os.path.normcase(os.path.normpath(profile_path))
        normalized_exclude_path = os.path.normcase(os.path.normpath(exclude_path))
        if (
            os.path.exists(profile_path)
            and (
                not normalized_exclude_path
                or normalized_profile_path != normalized_exclude_path
            )
        ):
            raise ValueError(
                f"Profile name '{normalized_name}' conflicts with existing file "
                f"'{os.path.basename(profile_path)}'."
            )
        return normalized_name, profile_path

    def _refresh_shared_profile_entries(self):
        shared_profiles_dir = self._get_shared_profiles_dir()
        os.makedirs(shared_profiles_dir, exist_ok=True)
        previous_selected_path = self.shared_profile_selected_path
        entries: list[SharedProfileSummary] = []
        load_failures: list[str] = []

        for filename in os.listdir(shared_profiles_dir):
            if not str(filename).lower().endswith(".json"):
                continue
            profile_path = os.path.join(shared_profiles_dir, filename)
            if not os.path.isfile(profile_path):
                continue
            try:
                entries.append(self._load_shared_profile_summary_from_path(profile_path))
            except Exception as exc:
                load_failures.append(f"{filename}: {exc}")

        entries.sort(
            key=lambda entry: (
                str(entry.display_name).casefold(),
                str(entry.filename).casefold(),
            )
        )
        self.shared_profile_entries = entries
        self.shared_profile_entries_loaded = True

        if load_failures:
            preview = " | ".join(load_failures[:3])
            if len(load_failures) > 3:
                preview = f"{preview} | ...and {len(load_failures) - 3} more."
            self.shared_profile_scan_warning = (
                f"Some shared profiles could not be loaded: {preview}"
            )
        else:
            self.shared_profile_scan_warning = ""

        normalized_previous_path = os.path.normcase(
            os.path.normpath(previous_selected_path)
        )
        matching_entry = next(
            (
                entry
                for entry in entries
                if os.path.normcase(os.path.normpath(entry.path))
                == normalized_previous_path
            ),
            None,
        )
        if matching_entry is not None:
            self._set_selected_shared_profile_path(matching_entry.path)
        elif entries:
            self._set_selected_shared_profile_path(entries[0].path)
        else:
            self._set_selected_shared_profile_path("")

    def _set_shared_profile_feedback(
        self,
        *,
        warning: str = "",
        notice: str = "",
    ):
        self.shared_profile_warning = str(warning or "").strip()
        self.shared_profile_notice = str(notice or "").strip()

    def _save_current_as_new_shared_profile(self):
        self._ensure_initialized()
        try:
            profile_name, profile_path = self._ensure_shared_profile_name_available(
                self.shared_profile_name_input
            )
            wrapper = self._build_shared_profile_wrapper(profile_name)
            self._write_profile_payload_to_path(profile_path, wrapper)
            self._refresh_shared_profile_entries()
            self._set_selected_shared_profile_path(profile_path)
            self._clear_shared_profile_confirmation_state()
            self._set_shared_profile_feedback(
                notice=f"Saved shared profile '{profile_name}'."
            )
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to save shared profile: {exc}"
            )

    def _rename_selected_shared_profile(self):
        self._ensure_initialized()
        selected_profile = self._get_selected_shared_profile()
        if selected_profile is None:
            self._set_shared_profile_feedback(
                warning="Select a shared profile to rename."
            )
            return

        try:
            new_name, new_path = self._ensure_shared_profile_name_available(
                self.shared_profile_name_input,
                exclude_path=selected_profile.path,
            )
            wrapper = self._build_shared_profile_wrapper(
                new_name,
                payload=selected_profile.payload,
                saved_at_unix_ms=selected_profile.saved_at_unix_ms,
            )
            self._write_profile_payload_to_path(new_path, wrapper)
            normalized_old_path = os.path.normcase(
                os.path.normpath(selected_profile.path)
            )
            normalized_new_path = os.path.normcase(os.path.normpath(new_path))
            if normalized_old_path != normalized_new_path and os.path.exists(
                selected_profile.path
            ):
                os.remove(selected_profile.path)
            self._refresh_shared_profile_entries()
            self._set_selected_shared_profile_path(new_path)
            self._clear_shared_profile_confirmation_state()
            self._set_shared_profile_feedback(
                notice=(
                    f"Renamed shared profile '{selected_profile.display_name}' "
                    f"to '{new_name}'."
                )
            )
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to rename shared profile: {exc}"
            )

    def _save_current_over_selected_shared_profile(self):
        self._ensure_initialized()
        selected_profile = self._get_selected_shared_profile()
        if selected_profile is None:
            self._set_shared_profile_feedback(
                warning="Select a shared profile to overwrite."
            )
            return

        try:
            wrapper = self._build_shared_profile_wrapper(selected_profile.display_name)
            self._write_profile_payload_to_path(selected_profile.path, wrapper)
            self._refresh_shared_profile_entries()
            self._set_selected_shared_profile_path(selected_profile.path)
            self._clear_shared_profile_confirmation_state()
            self._set_shared_profile_feedback(
                notice=(
                    f"Saved current Merchant Rules settings over "
                    f"'{selected_profile.display_name}'."
                )
            )
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to overwrite shared profile: {exc}"
            )

    def _load_selected_shared_profile(self):
        self._ensure_initialized()
        selected_profile = self._get_selected_shared_profile()
        if selected_profile is None:
            self._set_shared_profile_feedback(
                warning="Select a shared profile to load."
            )
            return

        try:
            self._write_profile_payload_for_account(
                self.account_key,
                selected_profile.payload,
                preserve_existing_window_geometry=True,
            )
            self.reload_profile_from_disk(
                status_message=(
                    f"Loaded shared profile '{selected_profile.display_name}' "
                    f"into the current Merchant Rules config."
                ),
                preserve_window_geometry=True,
                preserve_workspace_state=True,
            )
            self._refresh_shared_profile_entries()
            self._set_selected_shared_profile_path(selected_profile.path)
            self._clear_shared_profile_confirmation_state()
            self._set_shared_profile_feedback(
                notice=(
                    f"Loaded shared profile '{selected_profile.display_name}'. "
                    "Use Sync Rules to Selected when you want followers updated."
                )
            )
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to load shared profile: {exc}"
            )

    def _delete_selected_shared_profile(self):
        self._ensure_initialized()
        selected_profile = self._get_selected_shared_profile()
        if selected_profile is None:
            self._set_shared_profile_feedback(
                warning="Select a shared profile to delete."
            )
            return

        try:
            backup_path = self._refresh_adjacent_profile_backup(selected_profile.path)
            if os.path.exists(selected_profile.path):
                os.remove(selected_profile.path)
            self._refresh_shared_profile_entries()
            self._clear_shared_profile_confirmation_state()
            backup_label = os.path.basename(backup_path) if backup_path else ""
            notice = f"Deleted shared profile '{selected_profile.display_name}'."
            if backup_label:
                notice = f"{notice} Backup: {backup_label}."
            self._set_shared_profile_feedback(notice=notice)
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to delete shared profile: {exc}"
            )

    def _open_shared_profiles_folder(self) -> bool:
        folder_path = self._get_shared_profiles_dir()
        try:
            os.makedirs(folder_path, exist_ok=True)
            startfile = getattr(os, "startfile", None)
            if startfile is None:
                raise OSError("Opening folders is not supported on this platform.")
            startfile(folder_path)
            self.status_message = "Opened the shared Merchant Rules profiles folder."
            return True
        except Exception as exc:
            self._set_shared_profile_feedback(
                warning=f"Failed to open the shared profiles folder: {exc}"
            )
            ConsoleLog(
                MODULE_NAME,
                f"Failed to open shared profiles folder {folder_path}: {exc}",
                Console.MessageType.Error,
            )
            return False

    def _get_profile_recovery_dir(self, config_path: str) -> str:
        safe_config_path = str(config_path or "").strip()
        base_dir = os.path.dirname(safe_config_path) if safe_config_path else CONFIG_DIR
        return os.path.join(base_dir, "Recovery")

    def _get_adjacent_profile_backup_path(self, config_path: str) -> str:
        return f"{config_path}.bak"

    def _get_profile_backup_path(self, config_path: str) -> str:
        safe_config_path = str(config_path or "").strip()
        if not safe_config_path:
            return ""
        recovery_dir = self._get_profile_recovery_dir(safe_config_path)
        return os.path.join(recovery_dir, f"{os.path.basename(safe_config_path)}.bak")

    def _get_available_profile_backup_path(self, config_path: str) -> str:
        backup_path = self._get_profile_backup_path(config_path)
        if backup_path and os.path.exists(backup_path):
            return backup_path
        legacy_backup_path = self._get_adjacent_profile_backup_path(config_path)
        if legacy_backup_path and os.path.exists(legacy_backup_path):
            return legacy_backup_path
        return ""

    def _refresh_adjacent_profile_backup(self, config_path: str) -> str:
        if not os.path.exists(config_path):
            return ""
        backup_path = self._get_adjacent_profile_backup_path(config_path)
        shutil.copyfile(config_path, backup_path)
        return backup_path

    def _refresh_profile_backup(self, config_path: str) -> str:
        if not os.path.exists(config_path):
            return ""
        backup_path = self._get_profile_backup_path(config_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copyfile(config_path, backup_path)
        return backup_path

    def _list_failed_profile_snapshots(self, config_path: str) -> list[str]:
        safe_config_path = str(config_path or "").strip()
        if not safe_config_path:
            return []

        filename_prefix = f"{os.path.basename(safe_config_path)}.load-failed-"
        candidate_dirs = [
            self._get_profile_recovery_dir(safe_config_path),
            os.path.dirname(safe_config_path),
        ]
        snapshot_paths: list[str] = []
        seen_dirs: set[str] = set()
        for candidate_dir in candidate_dirs:
            normalized_dir = os.path.normcase(os.path.normpath(str(candidate_dir or "").strip()))
            if not normalized_dir or normalized_dir in seen_dirs or not os.path.isdir(candidate_dir):
                continue
            seen_dirs.add(normalized_dir)
            try:
                filenames = os.listdir(candidate_dir)
            except OSError:
                continue
            for filename in filenames:
                if not filename.startswith(filename_prefix) or not filename.endswith(".bak"):
                    continue
                snapshot_path = os.path.join(candidate_dir, filename)
                if os.path.isfile(snapshot_path):
                    snapshot_paths.append(snapshot_path)
        snapshot_paths.sort(
            key=lambda path: (os.path.getmtime(path), os.path.basename(path)),
            reverse=True,
        )
        return snapshot_paths

    def _prune_failed_profile_snapshots(self, config_path: str):
        if FAILED_PROFILE_SNAPSHOT_LIMIT <= 0:
            return
        snapshot_paths = self._list_failed_profile_snapshots(config_path)
        for stale_path in snapshot_paths[FAILED_PROFILE_SNAPSHOT_LIMIT:]:
            try:
                os.remove(stale_path)
            except OSError as exc:
                self._debug_log(
                    f"Merchant Rules could not prune stale recovery snapshot {stale_path}: {exc}"
                )

    def _migrate_legacy_recovery_artifacts(self):
        os.makedirs(RECOVERY_DIR, exist_ok=True)
        try:
            filenames = os.listdir(CONFIG_DIR)
        except OSError as exc:
            self._debug_log(
                f"Merchant Rules could not scan legacy recovery artifacts in {CONFIG_DIR}: {exc}"
            )
            return

        live_backup_pattern = re.compile(
            r"^MerchantRules_(?:[0-9a-f]{8}|default)\.json(?:\.load-failed-\d{8}-\d{6}-\d{3})?\.bak$"
        )
        for filename in filenames:
            if not live_backup_pattern.fullmatch(filename):
                continue
            legacy_path = os.path.join(CONFIG_DIR, filename)
            if not os.path.isfile(legacy_path):
                continue
            target_path = os.path.join(RECOVERY_DIR, filename)
            if os.path.exists(target_path):
                continue
            try:
                os.replace(legacy_path, target_path)
            except OSError as exc:
                self._debug_log(
                    f"Merchant Rules could not move legacy recovery artifact {legacy_path} -> {target_path}: {exc}"
                )

    def _snapshot_failed_profile(self, config_path: str) -> str:
        if not os.path.exists(config_path):
            return ""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        millis_suffix = int(time.time() * 1000) % 1000
        recovery_dir = self._get_profile_recovery_dir(config_path)
        os.makedirs(recovery_dir, exist_ok=True)
        snapshot_path = os.path.join(
            recovery_dir,
            f"{os.path.basename(config_path)}.load-failed-{timestamp}-{millis_suffix:03d}.bak",
        )
        shutil.copyfile(config_path, snapshot_path)
        self._prune_failed_profile_snapshots(config_path)
        return snapshot_path

    def _write_profile_payload_to_path(
        self,
        config_path: str,
        payload: dict[str, object],
        *,
        backup_mode: str = "adjacent",
    ):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        temp_path = f"{config_path}.tmp-{int(time.time() * 1000)}"
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=4)
                file.flush()
                os.fsync(file.fileno())
            if os.path.exists(config_path):
                if backup_mode == "recovery":
                    self._refresh_profile_backup(config_path)
                else:
                    self._refresh_adjacent_profile_backup(config_path)
            os.replace(temp_path, config_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _write_profile_payload_for_account(
        self,
        account_key: str,
        payload: dict[str, object],
        *,
        preserve_existing_window_geometry: bool = False,
    ) -> str:
        config_path = self._get_config_path_for_account(account_key)
        payload_to_write = dict(payload)
        if preserve_existing_window_geometry and os.path.exists(config_path):
            try:
                existing_payload = self._normalize_profile_payload(self._load_profile_from_path(config_path))
                for key in PROFILE_WINDOW_GEOMETRY_KEYS:
                    payload_to_write[key] = existing_payload.get(key)
            except Exception as exc:
                self._debug_log(f"Merchant Rules sync could not preserve follower window geometry from {config_path}: {exc}")
        for key, value in self._get_default_window_geometry_payload().items():
            payload_to_write.setdefault(key, value)
        self._write_profile_payload_to_path(
            config_path,
            payload_to_write,
            backup_mode="recovery",
        )
        return config_path

    def _load_profile_from_path(self, config_path: str) -> dict[str, object]:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _clear_preview_inventory_diff(self):
        self.preview_inventory_diff_summary = ""
        self.preview_inventory_diff_rows = []
        self.last_preview_compare_duration_ms = 0.0
        self.execute_drift_requires_confirmation = False

    def _clear_preview_projection_state(self):
        self.preview_requires_execute_travel = False
        self.preview_execute_travel_target_outpost_id = 0
        self.preview_execute_travel_target_outpost_name = ""

    def _set_preview_projection_state(
        self,
        *,
        requires_travel: bool = False,
        target_outpost_id: int = 0,
        target_outpost_name: str = "",
    ):
        if not requires_travel:
            self._clear_preview_projection_state()
            return
        self.preview_requires_execute_travel = True
        self.preview_execute_travel_target_outpost_id = max(0, int(target_outpost_id))
        self.preview_execute_travel_target_outpost_name = str(target_outpost_name or "").strip()

    def _preview_has_execute_travel_pending(self) -> bool:
        return bool(
            self.preview_ready
            and self.preview_requires_execute_travel
            and self.preview_execute_travel_target_outpost_id > 0
            and self.preview_execute_travel_target_outpost_name
        )

    def _clear_runtime_diagnostics(self):
        self.inventory_modifier_cache_hits = 0
        self.inventory_modifier_cache_misses = 0
        self.last_inventory_snapshot_duration_ms = 0.0
        self.last_plan_build_duration_ms = 0.0
        self.last_preview_compare_duration_ms = 0.0
        self.last_execution_phase_durations_ms = {}

    def _restore_profile_from_backup(self) -> bool:
        backup_path = self._get_available_profile_backup_path(self.config_path)
        if not backup_path or not os.path.exists(backup_path):
            self.profile_warning = "No Merchant Rules live config backup file was found to restore."
            return False
        try:
            raw_payload = self._load_profile_from_path(backup_path)
            raw_version = _safe_int(raw_payload.get("version", 0), 0) if isinstance(raw_payload, dict) else 0
            if raw_version > PROFILE_VERSION:
                raise ValueError(
                    f"Backup live config version {raw_version} is newer than this Merchant Rules version {PROFILE_VERSION}."
                )
            normalized_payload = self._normalize_profile_payload(raw_payload)
            self._write_profile_payload_to_path(
                self.config_path,
                normalized_payload,
                backup_mode="recovery",
            )
            self._load_profile()
            self._reset_runtime_after_profile_load(status_message="Merchant Rules live config restored from the last backup.")
            self.profile_warning = ""
            self.profile_notice = f"Restored live config from {os.path.basename(backup_path)}."
            return True
        except Exception as exc:
            self.profile_warning = f"Failed to restore Merchant Rules live config backup: {exc}"
            ConsoleLog(MODULE_NAME, f"Failed to restore backup {backup_path}: {exc}", Console.MessageType.Error)
            return False

    def _open_profile_config_folder(self) -> bool:
        folder_path = os.path.dirname(self.config_path) if self.config_path else CONFIG_DIR
        try:
            os.makedirs(folder_path, exist_ok=True)
            startfile = getattr(os, "startfile", None)
            if startfile is None:
                raise OSError("Opening folders is not supported on this platform.")
            startfile(folder_path)
            self.status_message = "Opened the Merchant Rules live config folder."
            return True
        except Exception as exc:
            self.profile_warning = f"Failed to open the Merchant Rules live config folder: {exc}"
            ConsoleLog(MODULE_NAME, f"Failed to open config folder {folder_path}: {exc}", Console.MessageType.Error)
            return False

    def _reset_runtime_after_profile_load(self, *, status_message: str = ""):
        self.preview_plan = PlanResult()
        self.preview_ready = False
        self._clear_preview_projection_state()
        self.last_error = ""
        self.last_execution_summary = ""
        self.last_cleanup_summary = ""
        self.last_instant_destroy_summary = ""
        self.destroy_instant_enabled = False
        self.destroy_include_protected_items = False
        self.auto_cleanup_running = False
        self.auto_cleanup_zone_attempted = False
        self.auto_cleanup_zone_token = ""
        self.cleanup_model_search_text = ""
        self.instant_destroy_running = False
        self.instant_destroy_rescan_requested = False
        self.instant_destroy_last_signature = ()
        self.instant_destroy_poll_timer.Reset()
        self._clear_sell_protection_jump("runtime reset after profile load")
        self._clear_preview_inventory_diff()
        self.map_ready_snapshot = bool(Map.IsMapReady())
        self.map_snapshot = int(Map.GetMapID() or 0) if self.map_ready_snapshot else 0
        self.map_instance_uptime_snapshot_ms = int(Map.GetInstanceUptime() or 0) if self.map_ready_snapshot else 0
        self._invalidate_supported_context_cache()
        if status_message:
            self.status_message = status_message

    def reload_profile_from_disk(
        self,
        *,
        status_message: str = "Merchant Rules live config reloaded from disk.",
        preserve_window_geometry: bool = False,
        preserve_workspace_state: bool = False,
    ):
        self._ensure_initialized()
        window_geometry_snapshot = self._snapshot_window_geometry_state() if preserve_window_geometry else None
        workspace_snapshot = self.active_workspace if preserve_workspace_state else ""
        rules_workspace_snapshot = self.active_rules_workspace if preserve_workspace_state else ""
        self._load_profile()
        if window_geometry_snapshot is not None:
            geometry_changed = self._restore_window_geometry_state(window_geometry_snapshot)
            if geometry_changed:
                self.window_geometry_dirty = True
                self.window_geometry_save_timer.Reset()
        if preserve_workspace_state:
            self.active_workspace = workspace_snapshot or self.active_workspace
            self.active_rules_workspace = rules_workspace_snapshot or self.active_rules_workspace
        self._reset_runtime_after_profile_load(status_message=status_message)
        return True

    def _ensure_initialized(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(self._get_shared_profiles_dir(), exist_ok=True)
        os.makedirs(RECOVERY_DIR, exist_ok=True)
        if not self.legacy_recovery_artifacts_migrated:
            self._migrate_legacy_recovery_artifacts()
            self.legacy_recovery_artifacts_migrated = True
        if not self.catalog_loaded:
            self._load_catalog()
        if not self.outpost_entries:
            self._load_outpost_entries()
        if not self.shared_profile_entries_loaded:
            self._refresh_shared_profile_entries()
        current_account = self._get_account_key()
        if not self.initialized or current_account != self.account_key:
            self.account_key = current_account
            self.config_path = self._get_config_path_for_account(current_account)
            self._load_profile()
            self._reset_runtime_after_profile_load()
            self.initialized = True

        current_map_ready = bool(Map.IsMapReady())
        current_map_id = int(Map.GetMapID() or 0) if current_map_ready else 0
        current_instance_uptime_ms = int(Map.GetInstanceUptime() or 0) if current_map_ready else 0
        map_changed = current_map_id != self.map_snapshot
        map_ready_changed = current_map_ready != self.map_ready_snapshot
        instance_changed = (
            current_map_ready
            and self.map_ready_snapshot
            and current_map_id == self.map_snapshot
            and current_instance_uptime_ms < self.map_instance_uptime_snapshot_ms
        )

        if map_changed:
            self.map_snapshot = current_map_id
            self.preview_ready = False
            self.preview_plan = PlanResult()
            self._clear_preview_projection_state()
            self._clear_preview_inventory_diff()

        if map_changed or map_ready_changed or instance_changed:
            self._invalidate_supported_context_cache()
            self.auto_cleanup_zone_attempted = False
            self.auto_cleanup_zone_token = (
                f"{current_map_id}:{current_instance_uptime_ms}"
                if current_map_ready
                else ""
            )

        self.map_ready_snapshot = current_map_ready
        self.map_snapshot = current_map_id
        self.map_instance_uptime_snapshot_ms = current_instance_uptime_ms

    def _rebuild_text_caches(self):
        self.sell_model_text_cache = {
            index: _format_model_ids(rule.model_ids)
            for index, rule in enumerate(self.sell_rules)
        }
        self.destroy_model_text_cache = {
            index: _format_model_ids(rule.model_ids)
            for index, rule in enumerate(self.destroy_rules)
        }

    def _refresh_rule_ui_caches(self):
        self._rebuild_text_caches()
        self.buy_model_search_cache.clear()
        self.buy_manual_model_id_cache.clear()
        self.buy_rune_search_cache.clear()
        self.buy_rune_profession_cache.clear()
        self.destroy_model_search_cache.clear()
        self.sell_model_search_cache.clear()
        self.sell_blacklist_search_cache.clear()
        self.sell_blacklist_import_feedback_cache.clear()
        self.sell_weapon_requirement_search_cache.clear()
        self.sell_weapon_mod_search_cache.clear()
        self.sell_rune_search_cache.clear()

    def _load_modifier_catalogs(self):
        self.weapon_mod_entries = []
        self.rune_entries = []
        self.weapon_mod_names = {}
        self.rune_names = {}

        for identifier, weapon_mod in sorted(MOD_DB.weapon_mods.items(), key=lambda row: row[1].name.lower() or row[0].lower()):
            display_name = str(weapon_mod.name or identifier).strip()
            entry = {"identifier": str(identifier), "name": display_name}
            self.weapon_mod_entries.append(entry)
            self.weapon_mod_names[str(identifier)] = display_name

        for identifier, rune in sorted(MOD_DB.runes.items(), key=lambda row: row[1].name.lower() or row[0].lower()):
            display_name = str(rune.name or identifier).strip()
            entry = {"identifier": str(identifier), "name": display_name}
            self.rune_entries.append(entry)
            self.rune_names[str(identifier)] = display_name

    def _load_rune_buy_catalog(self):
        self.rune_buy_entries = []
        self.rune_buy_entries_by_identifier = {}
        self.rune_buy_entries_by_profession = {}
        self.rune_buy_professions = []

        if not os.path.exists(RUNES_CATALOG_PATH):
            raise FileNotFoundError(f"Rune catalog missing: {RUNES_CATALOG_PATH}")

        with open(RUNES_CATALOG_PATH, "r", encoding="utf-8") as file:
            raw_catalog = json.load(file)

        if not isinstance(raw_catalog, dict):
            raise ValueError("Rune catalog must be a JSON object.")

        entries: list[dict[str, object]] = []
        for raw_identifier, raw_entry in raw_catalog.items():
            if not isinstance(raw_entry, dict):
                continue
            identifier = _normalize_rune_identifier(raw_entry.get("Identifier", raw_identifier))
            if not identifier:
                continue
            names = raw_entry.get("Names", {})
            if isinstance(names, dict):
                display_name = str(names.get("English", identifier) or identifier).strip()
            else:
                display_name = identifier
            profession = _normalize_rune_catalog_profession(raw_entry.get("Profession", "_None"))
            rarity = str(raw_entry.get("Rarity", "") or "").strip()
            mod_type = str(raw_entry.get("ModType", "") or "").strip()
            vendor_value = max(0, _safe_int(raw_entry.get("VendorValue", 0), 0))
            entry = {
                "identifier": identifier,
                "name": display_name,
                "profession": profession,
                "profession_label": _get_rune_profession_label(profession),
                "rarity": rarity,
                "mod_type": mod_type,
                "kind_label": _get_rune_kind_label(mod_type),
                "vendor_value": vendor_value,
            }
            entries.append(entry)

        entries.sort(
            key=lambda entry: (
                str(entry.get("profession_label", "")).lower(),
                _get_rune_kind_sort_key(entry.get("mod_type", "")),
                _get_rune_rarity_sort_key(entry.get("rarity", "")),
                str(entry.get("name", "")).lower(),
                str(entry.get("identifier", "")).lower(),
            )
        )
        grouped_entries: dict[str, list[dict[str, object]]] = {}
        for entry in entries:
            profession = str(entry.get("profession", "_None") or "_None")
            grouped_entries.setdefault(profession, []).append(entry)

        profession_order = sorted(
            grouped_entries.keys(),
            key=lambda profession: (
                0 if profession == "_None" else 1,
                _get_rune_profession_label(profession).lower(),
            ),
        )

        self.rune_buy_entries = entries
        self.rune_buy_entries_by_identifier = {
            str(entry.get("identifier", "")).strip(): entry
            for entry in entries
            if str(entry.get("identifier", "")).strip()
        }
        self.rune_buy_entries_by_profession = grouped_entries
        self.rune_buy_professions = profession_order

    def _debug_log(self, message: str):
        if not self.debug_logging:
            return
        debug_type = getattr(Console.MessageType, "Debug", Console.MessageType.Info)
        ConsoleLog(MODULE_NAME, str(message), debug_type)

    def _format_debug_coords(self, coords: tuple[float, float] | None) -> str:
        if coords is None:
            return "unresolved"
        try:
            return f"({float(coords[0]):.1f}, {float(coords[1]):.1f})"
        except Exception:
            return str(coords)

    def _get_catalog_alias_group_count(self) -> int:
        return sum(1 for model_ids in self.catalog_alias_to_model_ids.values() if len(model_ids) > 1)

    def _get_catalog_summary_text(self) -> str:
        final_models = int(self.catalog_stats.get("final_models", len(self.catalog_by_model_id)) or 0)
        alias_groups = int(self.catalog_stats.get("alias_groups", self._get_catalog_alias_group_count()) or 0)
        return f"Catalog: {final_models} models | Alias groups: {alias_groups}"

    def _log_catalog_summary(self, prefix: str):
        curated_total = int(self.catalog_stats.get("curated_total", 0) or 0)
        curated_common = int(self.catalog_stats.get("curated_common", 0) or 0)
        curated_rare = int(self.catalog_stats.get("curated_rare", 0) or 0)
        curated_essentials = int(self.catalog_stats.get("curated_essentials", 0) or 0)
        item_handling_present = bool(self.catalog_stats.get("item_handling_present", False))
        item_handling_items = int(self.catalog_stats.get("item_handling_items", 0) or 0)
        mirrored_present = bool(self.catalog_stats.get("mirrored_present", False))
        mirrored_items = int(self.catalog_stats.get("mirrored_items", 0) or 0)
        mirrored_fallback_used = bool(self.catalog_stats.get("mirrored_deprecated_fallback_used", False))
        drop_data = int(self.catalog_stats.get("drop_data", 0) or 0)
        modelid_fallback_items = int(self.catalog_stats.get("modelid_fallback_items", 0) or 0)
        final_models = int(self.catalog_stats.get("final_models", len(self.catalog_by_model_id)) or 0)
        alias_groups = int(self.catalog_stats.get("alias_groups", self._get_catalog_alias_group_count()) or 0)
        self._debug_log(
            f"{prefix}: curated={curated_total} (common={curated_common}, rare={curated_rare}, essentials={curated_essentials}) | "
            f"item_handling_present={item_handling_present} item_handling_items={item_handling_items} | "
            f"mirrored_present={mirrored_present} mirrored_items={mirrored_items} fallback_used={mirrored_fallback_used} | drop_data={drop_data} | "
            f"modelid_fallback_items={modelid_fallback_items} | "
            f"final_models={final_models} | alias_groups={alias_groups}"
        )
        if self.catalog_load_error:
            self._debug_log(f"{prefix}: load warnings -> {self.catalog_load_error}")

    def _log_plan_summary(self, prefix: str, plan: PlanResult):
        self._debug_log(
            f"{prefix}: supported={plan.supported_map} has_actions={plan.has_actions} "
            f"entries={len(plan.entries)} travel={plan.travel_to_outpost_id} "
            f"destroy={len(plan.destroy_actions) if plan.destroy_actions else len(plan.destroy_item_ids)} "
            f"merchant_stock={len(plan.merchant_stock_buys)} material_buys={len(plan.material_buys)} rune_buys={len(plan.rune_trader_buys)} "
            f"storage_transfers={len(plan.storage_transfers)} cleanup_transfers={len(plan.cleanup_transfers)} "
            f"storage_state={plan.storage_plan_state} "
            f"material_sales={len(plan.material_sales)} "
            f"merchant_sells={len(plan.merchant_sell_item_ids)} rune_trader_sells={len(plan.rune_trader_sales)} "
        )

    def _get_modifier_cache_hit_rate(self) -> float:
        total_lookups = max(0, int(self.inventory_modifier_cache_hits) + int(self.inventory_modifier_cache_misses))
        if total_lookups <= 0:
            return 0.0
        return (float(self.inventory_modifier_cache_hits) / float(total_lookups)) * 100.0

    def _compare_current_inventory_against_preview(self) -> bool:
        self._clear_preview_inventory_diff()
        if not self.preview_ready:
            self.preview_inventory_diff_summary = "Run Preview before comparing inventory drift."
            return False
        if not self.preview_plan.inventory_snapshot_captured:
            self.preview_inventory_diff_summary = "This preview did not capture an inventory snapshot to compare."
            return False

        started_at = time.perf_counter()
        current_items = self._collect_inventory_items()
        current_model_counts = self._get_inventory_model_counts(current_items)
        self.last_preview_compare_duration_ms = max(0.0, (time.perf_counter() - started_at) * 1000.0)

        preview_model_counts = dict(self.preview_plan.inventory_model_counts)
        changed_rows: list[tuple[int, str]] = []
        for model_id in sorted(set(preview_model_counts.keys()) | set(current_model_counts.keys())):
            preview_count = max(0, int(preview_model_counts.get(model_id, 0)))
            current_count = max(0, int(current_model_counts.get(model_id, 0)))
            if current_count == preview_count:
                continue
            delta = current_count - preview_count
            delta_prefix = "+" if delta > 0 else ""
            changed_rows.append(
                (
                    abs(delta),
                    f"{delta_prefix}{delta} {self._format_model_label(model_id)} (now {current_count}, preview {preview_count})",
                )
            )

        if not changed_rows:
            self.preview_inventory_diff_summary = (
                f"Current inventory still matches the last preview snapshot across {len(current_items)} stack(s)."
            )
            self.execute_drift_requires_confirmation = False
            return True

        changed_rows.sort(key=lambda row: (-row[0], row[1].lower()))
        self.preview_inventory_diff_rows = [label for _weight, label in changed_rows[:PREVIEW_DIFF_ROW_LIMIT]]
        total_changed = len(changed_rows)
        if total_changed > PREVIEW_DIFF_ROW_LIMIT:
            self.preview_inventory_diff_rows.append(f"...and {total_changed - PREVIEW_DIFF_ROW_LIMIT} more changed model(s).")
        self.preview_inventory_diff_summary = (
            f"Inventory changed since preview: {total_changed} model(s) differ from the last snapshot."
        )
        self.execute_drift_requires_confirmation = True
        return True

    def _queue_execute_now(self):
        self.execute_drift_requires_confirmation = False
        GLOBAL_CACHE.Coroutines.append(self._execute_now())

    def _queue_execute_here(self):
        self.execute_drift_requires_confirmation = False
        GLOBAL_CACHE.Coroutines.append(self._execute_now(local_only=True))

    def _queue_cleanup_now(self, *, auto_triggered: bool = False):
        if self.auto_cleanup_running:
            return
        self.auto_cleanup_running = True
        GLOBAL_CACHE.Coroutines.append(self._execute_cleanup_now(auto_triggered=auto_triggered))

    def _request_execute_now(self):
        if not self._compare_current_inventory_against_preview():
            self.status_message = self.preview_inventory_diff_summary or "Run Preview before executing merchant actions."
            return
        if self.preview_inventory_diff_rows:
            self.status_message = "Inventory changed since preview. Re-Preview or confirm Execute Anyway."
            return
        self._queue_execute_now()

    def _request_execute_here(self):
        if not self._compare_current_inventory_against_preview():
            self.status_message = self.preview_inventory_diff_summary or "Run Preview before executing merchant actions here."
            return
        if self.preview_inventory_diff_rows:
            self.status_message = "Inventory changed since preview. Re-Preview or confirm Execute Anyway."
            return
        self._queue_execute_here()

    def _reload_catalog(self):
        self.catalog_loaded = False
        self.catalog_load_error = ""
        self.catalog_by_model_id = {}
        self.catalog_alias_to_model_ids = {}
        self.catalog_alias_display_names = {}
        self.catalog_common_material_ids = []
        self.catalog_merchant_essentials = []
        self.catalog_rare_materials = []
        self.catalog_stats = {}
        self._load_catalog()
        self.status_message = "Catalog reloaded."
        self._log_catalog_summary("Catalog reloaded")

    def _invalidate_supported_context_cache(self):
        self.cached_context_map_id = -1
        self.cached_supported_context = None

    def _register_catalog_entry(
        self,
        model_id: int,
        name: str,
        item_type: str = "",
        material_type: str = "",
        source: str = "",
        priority: int = 100,
        extra: dict[str, object] | None = None,
    ):
        safe_model_id = max(0, _safe_int(model_id, 0))
        safe_name = str(name or "").strip()
        if safe_model_id <= 0 or not safe_name:
            return

        current = self.catalog_by_model_id.get(safe_model_id)
        if current is not None and int(current.get("priority", 999)) <= priority:
            return

        entry: dict[str, object] = {
            "model_id": safe_model_id,
            "name": safe_name,
            "item_type": str(item_type or "").strip(),
            "material_type": str(material_type or "").strip(),
            "source": source,
            "priority": int(priority),
        }
        if extra:
            for key, value in extra.items():
                if value not in (None, ""):
                    entry[key] = value

        self.catalog_by_model_id[safe_model_id] = entry

    def _load_catalog_group(
        self,
        entries: list[dict[str, object]],
        source: str,
        priority: int,
        default_item_type: str = "",
        default_material_type: str = "",
    ) -> list[dict[str, object]]:
        loaded_entries: list[dict[str, object]] = []
        for entry in entries:
            model_id = max(0, _safe_int(entry.get("model_id", 0), 0))
            if model_id <= 0:
                continue

            loaded_entry = {
                "model_id": model_id,
                "name": str(entry.get("name", "") or f"Model {model_id}"),
                "item_type": str(entry.get("item_type", default_item_type) or default_item_type),
                "material_type": str(entry.get("material_type", default_material_type) or default_material_type),
            }
            if "default_target" in entry:
                loaded_entry["default_target"] = max(0, _safe_int(entry.get("default_target", 0), 0))

            self._register_catalog_entry(
                model_id=model_id,
                name=str(loaded_entry["name"]),
                item_type=str(loaded_entry["item_type"]),
                material_type=str(loaded_entry["material_type"]),
                source=source,
                priority=priority,
                extra={"default_target": loaded_entry.get("default_target", 0)},
            )
            loaded_entries.append(loaded_entry)
        return loaded_entries

    def _load_drop_data_catalog(self) -> int:
        if not os.path.exists(DROP_DATA_PATH):
            return 0

        with open(DROP_DATA_PATH, "r", encoding="utf-8") as file:
            rows = json.load(file)

        loaded_count = 0
        for row in rows:
            model_id = _resolve_model_id_value(row.get("model_id", 0))
            name = str(row.get("name", "")).strip()
            if model_id <= 0 or not name:
                continue
            self._register_catalog_entry(
                model_id=model_id,
                name=name,
                item_type=str(row.get("group", "")).strip(),
                material_type=str(row.get("subgroup", "")).strip(),
                source="modelid_drop_data",
                priority=50,
            )
            loaded_count += 1
        return loaded_count

    def _load_item_handling_catalog(self) -> int:
        if not os.path.exists(ITEM_HANDLING_ITEMS_CATALOG_PATH):
            return 0

        with open(ITEM_HANDLING_ITEMS_CATALOG_PATH, "r", encoding="utf-8") as file:
            raw_catalog = json.load(file)

        loaded_count = 0
        for entry in _iter_item_handling_catalog_entries(raw_catalog):
            model_id = _resolve_model_id_value(entry.get("model_id", entry.get("ModelID", 0)))
            name = str(entry.get("name") or entry.get("Name") or "").strip()
            if model_id <= 0 or not name:
                continue

            item_type = str(entry.get("item_type") or entry.get("ItemType") or "").strip()
            skin = str(entry.get("skin") or entry.get("Skin") or "").strip()
            wiki_url = str(entry.get("wiki_url") or entry.get("WikiURL") or "").strip()
            category = str(entry.get("category") or "").strip()
            sub_category = str(entry.get("sub_category") or "").strip()
            raw_attributes = entry.get("attributes", [])
            attributes = (
                [str(attribute).strip() for attribute in raw_attributes if str(attribute or "").strip()]
                if isinstance(raw_attributes, list)
                else []
            )
            alias_labels = _build_catalog_alias_labels(name, skin, wiki_url)

            extra: dict[str, object] = {
                "alias_labels": alias_labels,
                "attributes": attributes,
            }
            if skin:
                extra["skin"] = skin
            if wiki_url:
                extra["wiki_url"] = wiki_url
            if category:
                extra["category"] = category
            if sub_category:
                extra["sub_category"] = sub_category

            self._register_catalog_entry(
                model_id=model_id,
                name=name,
                item_type=item_type,
                source="item_handling_items_catalog",
                priority=_get_mirrored_item_priority(item_type),
                extra=extra,
            )
            loaded_count += 1
        return loaded_count

    def _load_mirrored_item_catalog(self) -> int:
        if not os.path.exists(ITEMS_CATALOG_PATH):
            return 0

        with open(ITEMS_CATALOG_PATH, "r", encoding="utf-8") as file:
            raw_catalog = json.load(file)

        loaded_count = 0
        for entry in list(raw_catalog.get("items", [])):
            model_id = max(0, _safe_int(entry.get("model_id", 0), 0))
            name = str(entry.get("name", "")).strip()
            if model_id <= 0 or not name:
                continue

            item_type = str(entry.get("item_type", "")).strip()
            skin = str(entry.get("skin", "")).strip()
            wiki_url = str(entry.get("wiki_url", "")).strip()
            attributes = entry.get("attributes", [])
            alias_labels = _build_catalog_alias_labels(name, skin, wiki_url)

            extra: dict[str, object] = {
                "alias_labels": alias_labels,
            }
            if skin:
                extra["skin"] = skin
            if wiki_url:
                extra["wiki_url"] = wiki_url
            if isinstance(attributes, list) and attributes:
                extra["attributes"] = [str(attribute).strip() for attribute in attributes if str(attribute or "").strip()]

            self._register_catalog_entry(
                model_id=model_id,
                name=name,
                item_type=item_type,
                source="merchant_rules_items_catalog",
                priority=_get_mirrored_item_priority(item_type),
                extra=extra,
            )
            loaded_count += 1
        return loaded_count

    def _load_model_id_fallback_catalog(self) -> int:
        enum_names_by_model_id: dict[int, list[str]] = {}
        for enum_name, model_id in _iter_model_id_enum_members():
            if model_id <= 0:
                continue
            names = enum_names_by_model_id.setdefault(model_id, [])
            if enum_name not in names:
                names.append(enum_name)

        loaded_count = 0
        for model_id, enum_names in enum_names_by_model_id.items():
            if model_id in self.catalog_by_model_id:
                continue
            if not enum_names:
                continue

            display_name = _humanize_model_id_enum_name(enum_names[0]) or f"Model {model_id}"
            alias_labels = _build_catalog_alias_labels(display_name)
            for enum_name in enum_names:
                raw_name = str(enum_name or "").strip()
                if not raw_name:
                    continue
                alias_labels.setdefault(_normalize_catalog_search_text(raw_name), raw_name)
                humanized_name = _humanize_model_id_enum_name(raw_name)
                if humanized_name:
                    alias_labels.setdefault(_normalize_catalog_search_text(humanized_name), humanized_name)

            self._register_catalog_entry(
                model_id=model_id,
                name=display_name,
                item_type=_infer_model_id_fallback_item_type(enum_names, display_name),
                source="modelid_enum_fallback",
                priority=90,
                extra={
                    "alias_labels": alias_labels,
                    "enum_names": list(enum_names),
                },
            )
            loaded_count += 1
        return loaded_count

    def _rebuild_catalog_alias_index(self):
        self.catalog_alias_to_model_ids = {}
        self.catalog_alias_display_names = {}

        for model_id, entry in self.catalog_by_model_id.items():
            alias_labels = entry.get("alias_labels", {})
            normalized_alias_labels: dict[str, str] = {}
            if isinstance(alias_labels, dict):
                for raw_alias, display_name in alias_labels.items():
                    normalized_alias = _normalize_catalog_search_text(raw_alias)
                    if normalized_alias:
                        normalized_alias_labels[normalized_alias] = str(display_name or "").strip() or normalized_alias.title()

            name = str(entry.get("name", "")).strip()
            normalized_name = _normalize_catalog_search_text(name)
            if normalized_name and normalized_name not in normalized_alias_labels:
                normalized_alias_labels[normalized_name] = name

            entry["alias_labels"] = normalized_alias_labels
            for normalized_alias, display_name in normalized_alias_labels.items():
                alias_model_ids = self.catalog_alias_to_model_ids.setdefault(normalized_alias, [])
                if model_id not in alias_model_ids:
                    alias_model_ids.append(model_id)
                self.catalog_alias_display_names.setdefault(normalized_alias, display_name)

    def _load_catalog(self):
        self.catalog_by_model_id = {}
        self.catalog_alias_to_model_ids = {}
        self.catalog_alias_display_names = {}
        self.catalog_common_material_ids = []
        self.catalog_merchant_essentials = []
        self.catalog_rare_materials = []
        self.catalog_stats = {}
        self.catalog_load_error = ""
        load_errors: list[str] = []
        common_entries: list[dict[str, object]] = []
        rare_entries: list[dict[str, object]] = []
        merchant_entries: list[dict[str, object]] = []
        item_handling_items_count = 0
        mirrored_items_count = 0
        drop_data_count = 0
        model_id_fallback_count = 0
        item_handling_present = os.path.exists(ITEM_HANDLING_ITEMS_CATALOG_PATH)
        mirrored_present = os.path.exists(ITEMS_CATALOG_PATH)

        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as file:
                raw_catalog = json.load(file)

            materials = raw_catalog.get("materials", {})
            merchant_items = raw_catalog.get("merchant_items", {})

            common_entries = self._load_catalog_group(
                entries=list(materials.get("common", [])),
                source="merchant_rules_catalog.common",
                priority=0,
                default_item_type="material",
                default_material_type="common",
            )
            rare_entries = self._load_catalog_group(
                entries=list(materials.get("rare", [])),
                source="merchant_rules_catalog.rare",
                priority=0,
                default_item_type="material",
                default_material_type="rare",
            )
            merchant_entries = self._load_catalog_group(
                entries=list(merchant_items.get("essentials", [])),
                source="merchant_rules_catalog.essentials",
                priority=0,
            )

            self.catalog_common_material_ids = _dedupe_model_ids([int(entry["model_id"]) for entry in common_entries])
            self.catalog_rare_materials = rare_entries
            self.catalog_merchant_essentials = merchant_entries
        except Exception as exc:
            load_errors.append(f"Catalog load failed: {exc}")

        try:
            item_handling_items_count = self._load_item_handling_catalog()
        except Exception as exc:
            load_errors.append(f"ItemHandling item catalog load failed: {exc}")

        # Deprecated compatibility fallback. The ItemHandling catalog is the
        # primary broad item catalog; only read the old MR mirror if it failed
        # to contribute any searchable entries.
        if item_handling_items_count <= 0:
            try:
                mirrored_items_count = self._load_mirrored_item_catalog()
            except Exception as exc:
                load_errors.append(f"Deprecated mirrored item catalog load failed: {exc}")

        try:
            drop_data_count = self._load_drop_data_catalog()
        except Exception as exc:
            load_errors.append(f"Drop-data name load failed: {exc}")

        try:
            self._load_modifier_catalogs()
        except Exception as exc:
            load_errors.append(f"Modifier data load failed: {exc}")

        try:
            self._load_rune_buy_catalog()
        except Exception as exc:
            load_errors.append(f"Rune buy catalog load failed: {exc}")

        if MOD_DB_LOAD_ERROR:
            load_errors.append(MOD_DB_LOAD_ERROR)

        try:
            model_id_fallback_count = self._load_model_id_fallback_catalog()
        except Exception as exc:
            load_errors.append(f"ModelID fallback catalog load failed: {exc}")

        self._rebuild_catalog_alias_index()
        self.catalog_stats = {
            "curated_common": len(common_entries),
            "curated_rare": len(rare_entries),
            "curated_essentials": len(merchant_entries),
            "curated_total": len(common_entries) + len(rare_entries) + len(merchant_entries),
            "item_handling_present": item_handling_present,
            "item_handling_items": item_handling_items_count,
            "mirrored_present": mirrored_present,
            "mirrored_items": mirrored_items_count,
            "mirrored_deprecated_fallback_used": item_handling_items_count <= 0 and mirrored_items_count > 0,
            "drop_data": drop_data_count,
            "modelid_fallback_items": model_id_fallback_count,
            "final_models": len(self.catalog_by_model_id),
            "alias_groups": self._get_catalog_alias_group_count(),
        }
        self.catalog_loaded = True
        if load_errors:
            self.catalog_load_error = " | ".join(load_errors)
            ConsoleLog(MODULE_NAME, self.catalog_load_error, Console.MessageType.Warning)

    def _load_outpost_entries(self):
        outposts = dict(zip(Map.GetOutpostIDs(), Map.GetOutpostNames()))
        entries: list[dict[str, object]] = []
        for outpost_id, outpost_name in outposts.items():
            clean_name = str(outpost_name or "").replace("outpost", "").strip()
            if not clean_name:
                continue
            entries.append(
                {
                    "id": int(outpost_id),
                    "name": clean_name,
                }
            )

        entries.sort(key=self._get_outpost_sort_key)
        self.outpost_entries = entries

    def _normalize_outpost_ids(self, values: list[int]) -> list[int]:
        valid_ids = {int(entry.get("id", 0)) for entry in self.outpost_entries}
        normalized: list[int] = []
        seen: set[int] = set()
        for value in values:
            outpost_id = max(0, _safe_int(value, 0))
            if outpost_id <= 0 or outpost_id in seen or outpost_id not in valid_ids:
                continue
            seen.add(outpost_id)
            normalized.append(outpost_id)
        return normalized

    def _get_outpost_name(self, outpost_id: int) -> str:
        safe_outpost_id = max(0, _safe_int(outpost_id, 0))
        if safe_outpost_id <= 0:
            return ""
        for entry in self.outpost_entries:
            if int(entry.get("id", 0)) == safe_outpost_id:
                return str(entry.get("name", "")).strip()
        fallback_name = str(Map.GetMapName(safe_outpost_id) or "").replace("outpost", "").strip()
        return fallback_name

    def _get_guild_hall_target_ids(self) -> set[int]:
        guild_hall_ids: set[int] = set()
        for entry in self.outpost_entries:
            outpost_id = max(0, _safe_int(entry.get("id", 0), 0))
            outpost_name = str(entry.get("name", "")).strip()
            if outpost_id > 0 and outpost_name.startswith("Guild Hall -"):
                guild_hall_ids.add(outpost_id)
        return guild_hall_ids

    def _is_guild_hall_target(self, outpost_id: int) -> bool:
        safe_outpost_id = max(0, _safe_int(outpost_id, 0))
        if safe_outpost_id <= 0:
            return False
        if safe_outpost_id in self._get_guild_hall_target_ids():
            return True
        return self._get_outpost_name(safe_outpost_id).startswith("Guild Hall -")

    def _is_travel_target_reached(self, target_outpost_id: int, current_map_id: int | None = None) -> bool:
        safe_outpost_id = max(0, _safe_int(target_outpost_id, 0))
        if safe_outpost_id <= 0:
            return False
        if self._is_guild_hall_target(safe_outpost_id):
            return Map.IsGuildHall()
        if current_map_id is None:
            current_map_id = int(Map.GetMapID() or 0)
        return Map.IsMapIDMatch(int(current_map_id or 0), safe_outpost_id)

    def _get_preview_projection_target(self) -> tuple[int, str]:
        target_outpost_id = max(0, int(self.target_outpost_id)) if self.auto_travel_enabled else 0
        if target_outpost_id <= 0:
            return 0, ""
        target_outpost_name = self._get_outpost_name(target_outpost_id)
        if not target_outpost_name:
            return 0, ""
        if self._is_travel_target_reached(target_outpost_id):
            return 0, ""
        return target_outpost_id, target_outpost_name

    def _travel_to_target_outpost(self, target_outpost_id: int):
        safe_outpost_id = max(0, _safe_int(target_outpost_id, 0))
        if safe_outpost_id <= 0:
            return False

        target_outpost_name = self._get_outpost_name(safe_outpost_id)
        if self._is_travel_target_reached(safe_outpost_id):
            return True

        if self._is_guild_hall_target(safe_outpost_id):
            self._debug_log(f"Guild Hall travel requested: target={target_outpost_name} ({safe_outpost_id})")
            Map.TravelGH()
            deadline = time.monotonic() + (max(0, int(TRAVEL_TIMEOUT_MS)) / 1000.0)
            while time.monotonic() < deadline:
                if Map.IsGuildHall() and Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded():
                    return True
                yield from Routines.Yield.wait(100)
            return False

        travel_ok = yield from Routines.Yield.Map.TravelToOutpost(
            safe_outpost_id,
            log=False,
            timeout=TRAVEL_TIMEOUT_MS,
        )
        return bool(travel_ok)

    def _format_outpost_label(self, outpost_id: int) -> str:
        safe_outpost_id = max(0, _safe_int(outpost_id, 0))
        if safe_outpost_id <= 0:
            return "Current Outpost"
        outpost_name = self._get_outpost_name(safe_outpost_id)
        if outpost_name:
            return f"{outpost_name} ({safe_outpost_id})"
        return f"Outpost {safe_outpost_id}"

    def _get_outpost_selector_guidance(self, outpost_id: int) -> str:
        safe_outpost_id = max(0, _safe_int(outpost_id, 0))
        if safe_outpost_id <= 0:
            return ""
        if safe_outpost_id in SUPPORTED_MAP_NPC_SELECTORS:
            return "Uses map-specific merchant selectors."
        return "Uses generic merchant selectors and depends on runtime NPC resolution."

    def _get_pinned_outpost_group_label(self, outpost_name: str) -> str:
        base_name = str(outpost_name or "").strip().split(" - ", 1)[0].strip()
        normalized_base_name = _normalize_outpost_match_text(base_name)
        if not normalized_base_name:
            return ""
        for group_label, aliases in TRAVEL_PINNED_OUTPOST_GROUPS:
            for alias in aliases:
                if normalized_base_name == _normalize_outpost_match_text(alias):
                    return group_label
        return ""

    def _get_default_visible_outpost_entries(self) -> list[dict[str, object]]:
        pinned_matches: list[tuple[tuple[str, int, int], dict[str, object]]] = []
        for entry in self.outpost_entries:
            outpost_id = int(entry.get("id", 0))
            outpost_name = str(entry.get("name", "")).strip()
            group_label = self._get_pinned_outpost_group_label(outpost_name)
            if outpost_id <= 0 or not group_label:
                continue
            variant_rank = 0 if " - " not in outpost_name else 1
            pinned_matches.append(((group_label.lower(), variant_rank, outpost_id), entry))
        pinned_matches.sort(key=lambda match: match[0])
        return [entry for _, entry in pinned_matches]

    def _get_outpost_sort_key(self, entry: dict[str, object]) -> tuple[int, int, int, str]:
        outpost_id = int(entry.get("id", 0))
        name = str(entry.get("name", "")).strip().lower()
        favorite_rank = 0 if outpost_id in self.favorite_outpost_ids else 1
        support_rank = 0 if outpost_id in SUPPORTED_MAP_NPC_SELECTORS else 1
        priority_rank = 0 if self._get_pinned_outpost_group_label(str(entry.get("name", ""))) else 1
        return favorite_rank, support_rank, priority_rank, name

    def _search_outposts(self, raw_query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, object]]:
        query = str(raw_query or "").strip().lower()
        if not query:
            return self._get_default_visible_outpost_entries()

        matches: list[tuple[tuple[int, int, int, int], dict[str, object]]] = []
        for entry in self.outpost_entries:
            outpost_id = int(entry.get("id", 0))
            name = str(entry.get("name", "")).strip()
            if outpost_id <= 0 or not name:
                continue

            id_text = str(outpost_id)
            name_lower = name.lower()
            initials = "".join(part[0] for part in name_lower.split() if part)
            if query not in name_lower and query not in id_text and query not in initials:
                continue

            score = (
                0 if outpost_id in self.favorite_outpost_ids else 1,
                0 if query == id_text else 1,
                0 if name_lower.startswith(query) else 1,
                0 if query == initials else 1,
                0 if outpost_id in SUPPORTED_MAP_NPC_SELECTORS else 1,
                0 if self._get_pinned_outpost_group_label(name) else 1,
                len(name_lower),
            )
            matches.append((score, entry))

        matches.sort(key=lambda match: match[0])
        return [entry for _, entry in matches[: max(1, int(limit))]]

    def _draw_outpost_search_results(self, child_id: str, query: str) -> int:
        results = self._search_outposts(query)
        picked_outpost_id = 0
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching outposts found.")
            else:
                for entry in results:
                    outpost_id = int(entry.get("id", 0))
                    label = self._format_outpost_label(outpost_id)
                    if PyImGui.selectable(f"{label}##{child_id}_{outpost_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_outpost_id = outpost_id
                        break
        PyImGui.end_child()
        return picked_outpost_id

    def _get_model_entry(self, model_id: int) -> dict[str, object] | None:
        return self.catalog_by_model_id.get(max(0, _safe_int(model_id, 0)))

    def _get_model_name(self, model_id: int) -> str:
        entry = self._get_model_entry(model_id)
        if entry is None:
            return ""
        return str(entry.get("name", "")).strip()

    def _format_model_label(self, model_id: int) -> str:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return "No item selected"
        name = self._get_model_name(safe_model_id)
        if name:
            return f"{name} ({safe_model_id})"
        return f"Model {safe_model_id}"

    def _get_model_descriptor(self, model_id: int) -> str:
        entry = self._get_model_entry(model_id)
        if entry is None:
            return ""
        material_type = str(entry.get("material_type", "")).strip()
        if material_type:
            return material_type
        return str(entry.get("item_type", "")).strip()

    def _get_model_item_type(self, model_id: int) -> str:
        entry = self._get_model_entry(model_id)
        if entry is None:
            return ""
        return str(entry.get("item_type", "")).strip()

    def _humanize_model_attribute_label(self, raw_value: object) -> str:
        label = str(raw_value or "").strip()
        if not label:
            return ""
        label = label.replace("_", " ")
        label = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", label)
        label = re.sub(r"\s+", " ", label).strip()
        if not label or label.casefold() == "none":
            return ""
        return label

    def _get_meaningful_model_attribute_labels(self, model_id: int) -> list[str]:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return []
        item_type = self._get_model_item_type(safe_model_id)
        if not _is_weapon_catalog_item_type(item_type):
            return []

        entry = self._get_model_entry(safe_model_id)
        if entry is None:
            return []

        raw_attributes = entry.get("attributes", [])
        if not isinstance(raw_attributes, list):
            return []

        labels: list[str] = []
        seen_labels: set[str] = set()
        for raw_attribute in raw_attributes:
            humanized_label = self._humanize_model_attribute_label(raw_attribute)
            if not humanized_label:
                continue
            normalized_label = humanized_label.casefold()
            if normalized_label in seen_labels:
                continue
            seen_labels.add(normalized_label)
            labels.append(humanized_label)
        return labels

    def _get_model_attribute_suffix_from_model_id(self, model_id: int) -> str:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return ""
        item_type = self._get_model_item_type(safe_model_id)
        if not _is_weapon_catalog_item_type(item_type):
            return ""

        for member_name, member in getattr(ModelID, "__members__", {}).items():
            try:
                member_value = int(member.value)
            except Exception:
                member_value = _safe_int(member, 0)
            if member_value != safe_model_id:
                continue

            normalized_member_name = str(member_name or "").strip()
            if not normalized_member_name:
                continue

            for suffix_key in MODEL_ID_ATTRIBUTE_FALLBACK_SUFFIX_KEYS:
                if (
                    normalized_member_name.endswith(f"_{suffix_key}")
                    or normalized_member_name.endswith(suffix_key)
                ):
                    return MODEL_ID_ATTRIBUTE_FALLBACK_LABELS.get(suffix_key, "")

        return ""

    def _get_single_model_attribute_suffix(self, model_id: int) -> str:
        attribute_labels = self._get_meaningful_model_attribute_labels(model_id)
        if len(attribute_labels) == 1:
            return attribute_labels[0]
        if len(attribute_labels) > 1:
            return ""
        return self._get_model_attribute_suffix_from_model_id(model_id)

    def _append_model_attribute_suffix(self, label: str, model_id: int) -> str:
        safe_label = str(label or "").strip()
        if not safe_label:
            return safe_label
        suffix = self._get_single_model_attribute_suffix(model_id)
        if not suffix:
            return safe_label
        return f"{safe_label} - {suffix}"

    def _format_model_label_long(self, model_id: int) -> str:
        label = self._format_model_label(model_id)
        item_type = self._get_model_item_type(model_id)
        if item_type:
            label = f"{label} [{item_type}]"
        return self._append_model_attribute_suffix(label, model_id)

    def _format_model_label_short(self, model_id: int) -> str:
        return self._append_model_attribute_suffix(self._format_model_label(model_id), model_id)

    def _extract_preview_label_model_id(self, label: str) -> int:
        safe_label = str(label or "").strip()
        if not safe_label:
            return 0

        model_match = re.fullmatch(r"Model\s+(\d+)", safe_label)
        if model_match is not None:
            return max(0, _safe_int(model_match.group(1), 0))

        named_match = re.fullmatch(r".+\s\((\d+)\)", safe_label)
        if named_match is None:
            return 0

        model_id = max(0, _safe_int(named_match.group(1), 0))
        if model_id <= 0 or self._get_model_entry(model_id) is None:
            return 0
        return model_id

    def _format_preview_item_label(self, entry: ExecutionPlanEntry) -> str:
        stored_label = str(getattr(entry, "label", "") or "").strip()
        explicit_model_id = max(0, _safe_int(getattr(entry, "model_id", 0), 0))
        model_id = explicit_model_id if explicit_model_id > 0 else self._extract_preview_label_model_id(stored_label)
        if model_id <= 0:
            return stored_label

        catalog_name = str(self._get_model_name(model_id) or "").strip()
        label_without_model = stored_label
        named_match = re.fullmatch(r"(.+?)\s\((\d+)\)", stored_label)
        if named_match is not None and max(0, _safe_int(named_match.group(2), 0)) == model_id:
            label_without_model = str(named_match.group(1) or "").strip()

        if not catalog_name:
            generic_label = f"Model {model_id}".casefold()
            if label_without_model and label_without_model.casefold() != generic_label:
                catalog_name = label_without_model
            elif stored_label and stored_label.casefold() != generic_label:
                catalog_name = stored_label

        if not catalog_name:
            return f"Model {model_id}"

        descriptor = self._get_model_descriptor(model_id)
        if descriptor:
            return self._append_model_attribute_suffix(f"{catalog_name} ({model_id}) [{descriptor}]", model_id)
        return self._append_model_attribute_suffix(f"{catalog_name} ({model_id})", model_id)

    def _get_weapon_mod_label(self, identifier: str) -> str:
        safe_identifier = str(identifier or "").strip()
        if not safe_identifier:
            return "Unknown Weapon Mod"
        return self.weapon_mod_names.get(safe_identifier, safe_identifier)

    def _get_rune_label(self, identifier: str) -> str:
        safe_identifier = str(identifier or "").strip()
        if not safe_identifier:
            return "Unknown Rune"
        return self.rune_names.get(safe_identifier, safe_identifier)

    def _get_rune_buy_entry(self, identifier: str) -> dict[str, object] | None:
        safe_identifier = _normalize_rune_identifier(identifier)
        if not safe_identifier:
            return None
        return self.rune_buy_entries_by_identifier.get(safe_identifier)

    def _get_common_material_preset(self) -> list[int]:
        return list(self.catalog_common_material_ids)

    def _get_rare_material_preset(self) -> list[int]:
        return _dedupe_model_ids([int(entry.get("model_id", 0)) for entry in self.catalog_rare_materials])

    def _get_common_material_catalog_entries(self) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        for model_id in self.catalog_common_material_ids:
            entry = self._get_model_entry(model_id)
            if entry is not None:
                entries.append(entry)
        return entries

    def _get_rare_material_catalog_entries(self) -> list[dict[str, object]]:
        return list(self.catalog_rare_materials)

    def _get_material_catalog_entry(self, model_id: int) -> dict[str, object] | None:
        entry = self._get_model_entry(model_id)
        if entry is None:
            return None
        material_type = str(entry.get("material_type", "")).strip().lower()
        if material_type not in {"common", "rare"}:
            return None
        return entry

    def _get_material_merchant_type_by_model(self, model_id: int) -> str:
        if _is_rare_crafting_material_model(model_id):
            return MERCHANT_TYPE_RARE_MATERIALS
        return MERCHANT_TYPE_MATERIALS

    def _get_sell_material_merchant_types(self, model_ids: list[int]) -> list[str]:
        merchant_types: list[str] = []
        for model_id in _dedupe_model_ids(model_ids):
            if self._get_material_catalog_entry(int(model_id)) is None:
                continue
            merchant_type = self._get_material_merchant_type_by_model(model_id)
            if merchant_type not in merchant_types:
                merchant_types.append(merchant_type)
        if merchant_types:
            return merchant_types
        return [MERCHANT_TYPE_MATERIALS, MERCHANT_TYPE_RARE_MATERIALS]

    def _get_material_batch_size(self, model_id: int) -> int:
        return _get_material_batch_size_for_model(model_id)

    def _get_explicit_sell_destination(self, item: InventoryItemInfo) -> str:
        if item.is_material:
            return self._get_material_merchant_type_by_model(item.model_id)
        if item.standalone_kind == RUNE_STANDALONE_KIND:
            return MERCHANT_TYPE_RUNE_TRADER
        return MERCHANT_TYPE_MERCHANT

    def _get_merchant_essential(self, model_id: int) -> dict[str, object] | None:
        safe_model_id = max(0, _safe_int(model_id, 0))
        for entry in self.catalog_merchant_essentials:
            if int(entry.get("model_id", 0)) == safe_model_id:
                return entry
        return None

    def _catalog_entry_matches_common_material(self, entry: dict[str, object]) -> bool:
        return str(entry.get("material_type", "")).strip().lower() == "common"

    def _catalog_entry_matches_weapon_blacklist(self, entry: dict[str, object]) -> bool:
        item_type = str(entry.get("item_type", "")).strip()
        if _is_weapon_catalog_item_type(item_type):
            return True
        return str(item_type).strip().lower() == "rune_mod" and _is_weapon_mod_catalog_name(entry.get("name", ""))

    def _catalog_entry_matches_armor_blacklist(
        self,
        entry: dict[str, object],
        *,
        include_standalone_runes: bool = False,
    ) -> bool:
        item_type = str(entry.get("item_type", "")).strip().lower()
        if item_type == "salvage":
            if _is_armor_rune_catalog_name(entry.get("name", "")):
                return include_standalone_runes
            return _is_armor_salvage_catalog_name(entry.get("name", ""))
        if _is_armor_catalog_item_type(item_type):
            return True
        if not include_standalone_runes or item_type != "rune_mod":
            return False
        return _is_armor_rune_catalog_name(entry.get("name", ""))

    def _search_catalog(self, raw_query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, object]]:
        query = _normalize_catalog_search_text(raw_query)
        if not query:
            return []

        matches: list[tuple[tuple[int, int, int, int, int, int, int], dict[str, object]]] = []
        for entry in self.catalog_by_model_id.values():
            name = str(entry.get("name", "")).strip()
            model_id = max(0, _safe_int(entry.get("model_id", 0), 0))
            if model_id <= 0 or not name:
                continue

            item_type = _normalize_catalog_search_text(entry.get("item_type", ""))
            material_type = _normalize_catalog_search_text(entry.get("material_type", ""))
            model_id_text = str(model_id)
            name_lower = _normalize_catalog_search_text(name)
            alias_labels = entry.get("alias_labels", {})
            alias_matches: list[str] = []
            if isinstance(alias_labels, dict):
                alias_matches = [
                    normalized_alias
                    for normalized_alias in alias_labels.keys()
                    if query in str(normalized_alias or "")
                ]
            if (
                query not in name_lower
                and query not in model_id_text
                and query not in item_type
                and query not in material_type
                and not alias_matches
            ):
                continue

            exact_alias_hit = any(alias == query for alias in alias_matches)
            prefix_alias_hit = any(alias.startswith(query) for alias in alias_matches)
            score = (
                0 if query == model_id_text else 1,
                0 if name_lower.startswith(query) else 1,
                0 if query in name_lower else 1,
                0 if exact_alias_hit else 1,
                0 if prefix_alias_hit else 1,
                0 if alias_matches else 1,
                0 if query in item_type or query in material_type else 1,
                len(name),
            )
            matches.append((score, entry))

        matches.sort(key=lambda match: match[0])
        return [entry for _, entry in matches[: max(1, int(limit))]]

    def _search_catalog_with_predicate(
        self,
        raw_query: str,
        *,
        entry_predicate: Callable[[dict[str, object]], bool],
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> list[dict[str, object]]:
        catalog_limit = max(max(1, len(self.catalog_by_model_id)), limit * 4, SEARCH_RESULT_LIMIT * 4)
        results = self._search_catalog(raw_query, limit=catalog_limit)
        filtered_results: list[dict[str, object]] = []
        seen_model_ids: set[int] = set()
        for entry in results:
            model_id = max(0, _safe_int(entry.get("model_id", 0), 0))
            if model_id <= 0 or model_id in seen_model_ids:
                continue
            if not entry_predicate(entry):
                continue
            seen_model_ids.add(model_id)
            filtered_results.append(entry)
            if len(filtered_results) >= max(1, int(limit)):
                break
        return filtered_results

    def _search_material_catalog(self, raw_query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, object]]:
        results = self._search_catalog(raw_query, limit=max(limit * 3, limit))
        material_results: list[dict[str, object]] = []
        for entry in results:
            if self._get_material_catalog_entry(int(entry.get("model_id", 0))) is None:
                continue
            material_results.append(entry)
            if len(material_results) >= max(1, int(limit)):
                break
        return material_results

    def _search_weapon_catalog(self, raw_query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, object]]:
        catalog_limit = max(max(1, len(self.catalog_by_model_id)), limit * 4, SEARCH_RESULT_LIMIT * 4)
        results = self._search_catalog(raw_query, limit=catalog_limit)
        weapon_results: list[dict[str, object]] = []
        seen_model_ids: set[int] = set()
        for entry in results:
            model_id = max(0, _safe_int(entry.get("model_id", 0), 0))
            if model_id <= 0 or model_id in seen_model_ids:
                continue
            if not _is_weapon_catalog_item_type(entry.get("item_type", "")):
                continue
            seen_model_ids.add(model_id)
            weapon_results.append(entry)
            if len(weapon_results) >= max(1, int(limit)):
                break
        return weapon_results

    def _search_common_material_catalog(self, raw_query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, object]]:
        return self._search_catalog_with_predicate(
            raw_query,
            entry_predicate=self._catalog_entry_matches_common_material,
            limit=limit,
        )

    def _search_catalog_alias_groups(
        self,
        raw_query: str,
        *,
        exclude_model_ids: list[int] | None = None,
        entry_predicate: Callable[[dict[str, object]], bool] | None = None,
        limit: int = SEARCH_RESULT_LIMIT,
    ) -> list[dict[str, object]]:
        query = _normalize_catalog_search_text(raw_query)
        if not query:
            return []

        excluded_ids = set(_dedupe_model_ids(exclude_model_ids or []))
        matches: list[tuple[tuple[int, int, int, int], dict[str, object]]] = []
        for normalized_alias, model_ids in self.catalog_alias_to_model_ids.items():
            if len(model_ids) < 2 or query not in normalized_alias:
                continue

            remaining_model_ids = [model_id for model_id in model_ids if model_id not in excluded_ids]
            if entry_predicate is not None:
                remaining_model_ids = [
                    model_id
                    for model_id in remaining_model_ids
                    if entry_predicate(self.catalog_by_model_id.get(model_id, {}))
                ]
            if len(remaining_model_ids) < 2:
                continue

            display_name = self.catalog_alias_display_names.get(normalized_alias, normalized_alias.title())
            score = (
                0 if normalized_alias == query else 1,
                0 if normalized_alias.startswith(query) else 1,
                len(remaining_model_ids),
                len(display_name),
            )
            matches.append(
                (
                    score,
                    {
                        "alias": normalized_alias,
                        "display_name": display_name,
                        "model_ids": remaining_model_ids,
                    },
                )
            )

        matches.sort(key=lambda match: match[0])
        return [entry for _, entry in matches[: max(1, int(limit))]]

    def _search_identifier_catalog(self, raw_query: str, entries: list[dict[str, str]], limit: int = SEARCH_RESULT_LIMIT) -> list[dict[str, str]]:
        query = str(raw_query or "").strip().lower()
        if not query:
            return []

        matches: list[tuple[tuple[int, int, int], dict[str, str]]] = []
        for entry in entries:
            identifier = str(entry.get("identifier", "")).strip()
            name = str(entry.get("name", "")).strip()
            if not identifier or not name:
                continue

            identifier_lower = identifier.lower()
            name_lower = name.lower()
            if query not in identifier_lower and query not in name_lower:
                continue

            score = (
                0 if name_lower.startswith(query) else 1,
                0 if query in name_lower else 1,
                len(name_lower),
            )
            matches.append((score, entry))

        matches.sort(key=lambda match: match[0])
        return [entry for _, entry in matches[: max(1, int(limit))]]

    def _set_buy_rule_merchant_stock_targets(self, rule: BuyRule, merchant_stock_targets: list[MerchantStockTarget]) -> bool:
        normalized_targets = _normalize_merchant_stock_targets(merchant_stock_targets)
        current_targets = _normalize_merchant_stock_targets(rule.merchant_stock_targets)
        if normalized_targets == current_targets:
            return False
        rule.merchant_stock_targets = normalized_targets
        return True

    def _add_buy_rule_merchant_stock_target(
        self,
        rule: BuyRule,
        model_id: int,
        *,
        target_count: int = 0,
        max_per_run: int = 0,
    ) -> bool:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return False

        existing_targets = _normalize_merchant_stock_targets(rule.merchant_stock_targets)
        for merchant_stock_target in existing_targets:
            if merchant_stock_target.model_id == safe_model_id:
                return False

        existing_targets.append(
            MerchantStockTarget(
                model_id=safe_model_id,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )
        return self._set_buy_rule_merchant_stock_targets(rule, existing_targets)

    def _set_buy_rule_material_targets(self, rule: BuyRule, material_targets: list[MaterialTarget]) -> bool:
        normalized_targets = _normalize_material_targets(material_targets)
        current_targets = _normalize_material_targets(rule.material_targets)
        if normalized_targets == current_targets:
            return False
        rule.material_targets = normalized_targets
        return True

    def _add_buy_rule_material_target(
        self,
        rule: BuyRule,
        model_id: int,
        *,
        target_count: int = 0,
        max_per_run: int = 0,
    ) -> bool:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return False

        existing_targets = _normalize_material_targets(rule.material_targets)
        for material_target in existing_targets:
            if material_target.model_id == safe_model_id:
                return False

        existing_targets.append(
            MaterialTarget(
                model_id=safe_model_id,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )
        return self._set_buy_rule_material_targets(rule, existing_targets)

    def _set_buy_rule_rune_targets(self, rule: BuyRule, rune_targets: list[RuneTraderTarget]) -> bool:
        normalized_targets = _normalize_rune_trader_targets(rune_targets)
        current_targets = _normalize_rune_trader_targets(rule.rune_targets)
        if normalized_targets == current_targets:
            return False
        rule.rune_targets = normalized_targets
        return True

    def _add_buy_rule_rune_target(
        self,
        rule: BuyRule,
        identifier: str,
        *,
        target_count: int = 0,
        max_per_run: int = 0,
    ) -> bool:
        safe_identifier = _normalize_rune_identifier(identifier)
        if not safe_identifier:
            return False

        existing_targets = _normalize_rune_trader_targets(rule.rune_targets)
        for rune_target in existing_targets:
            if rune_target.identifier == safe_identifier:
                return False

        existing_targets.append(
            RuneTraderTarget(
                identifier=safe_identifier,
                target_count=max(0, _safe_int(target_count, 0)),
                max_per_run=max(0, _safe_int(max_per_run, 0)),
            )
        )
        return self._set_buy_rule_rune_targets(rule, existing_targets)

    def _set_sell_rule_whitelist_targets(self, index: int, rule: SellRule, whitelist_targets: list[WhitelistTarget]) -> bool:
        normalized_targets = _normalize_whitelist_targets(whitelist_targets)
        current_targets = _normalize_whitelist_targets(getattr(rule, "whitelist_targets", []))
        normalized_ids = _get_whitelist_target_model_ids(normalized_targets)
        self.sell_model_text_cache[index] = _format_model_ids(normalized_ids)
        if normalized_targets == current_targets:
            return False
        rule.whitelist_targets = normalized_targets
        rule.model_ids = normalized_ids
        rule.keep_count = 0
        return True

    def _set_sell_rule_model_ids(self, index: int, rule: SellRule, model_ids: list[int]) -> bool:
        next_targets = _build_whitelist_targets_from_model_ids(
            model_ids,
            getattr(rule, "whitelist_targets", []),
            default_keep_count=max(0, int(getattr(rule, "keep_count", 0))),
        )
        return self._set_sell_rule_whitelist_targets(index, rule, next_targets)

    def _set_destroy_rule_whitelist_targets(self, index: int, rule: DestroyRule, whitelist_targets: list[WhitelistTarget]) -> bool:
        normalized_targets = _normalize_whitelist_targets(whitelist_targets)
        current_targets = _normalize_whitelist_targets(getattr(rule, "whitelist_targets", []))
        normalized_ids = _get_whitelist_target_model_ids(normalized_targets)
        self.destroy_model_text_cache[index] = _format_model_ids(normalized_ids)
        if normalized_targets == current_targets:
            return False
        rule.whitelist_targets = normalized_targets
        rule.model_ids = normalized_ids
        rule.keep_count = 0
        return True

    def _set_destroy_rule_model_ids(self, index: int, rule: DestroyRule, model_ids: list[int]) -> bool:
        next_targets = _build_whitelist_targets_from_model_ids(
            model_ids,
            getattr(rule, "whitelist_targets", []),
            default_keep_count=max(0, int(getattr(rule, "keep_count", 0))),
        )
        return self._set_destroy_rule_whitelist_targets(index, rule, next_targets)

    def _set_cleanup_targets(self, cleanup_targets: list[CleanupTarget]) -> bool:
        normalized_targets = _normalize_cleanup_targets(cleanup_targets)
        if normalized_targets == self.cleanup_targets:
            return False
        self.cleanup_targets = normalized_targets
        return True

    def _add_cleanup_target(self, model_id: int, *, keep_on_character: int = 0) -> bool:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return False
        existing_targets = _normalize_cleanup_targets(self.cleanup_targets)
        for target in existing_targets:
            if int(target.model_id) == safe_model_id:
                return False
        existing_targets.append(
            CleanupTarget(
                model_id=safe_model_id,
                keep_on_character=max(0, _safe_int(keep_on_character, 0)),
            )
        )
        return self._set_cleanup_targets(existing_targets)

    def _set_cleanup_protection_sources(self, cleanup_sources: list[CleanupProtectionSource]) -> bool:
        normalized_sources = _normalize_cleanup_protection_sources(cleanup_sources)
        if normalized_sources == self.cleanup_protection_sources:
            return False
        self.cleanup_protection_sources = normalized_sources
        return True

    def _add_cleanup_protection_source(self, sell_rule_id: object) -> bool:
        safe_rule_id = _normalize_rule_id(sell_rule_id)
        if not safe_rule_id:
            return False
        existing_sources = _normalize_cleanup_protection_sources(self.cleanup_protection_sources)
        for source in existing_sources:
            if str(source.sell_rule_id) == safe_rule_id:
                return False
        existing_sources.append(CleanupProtectionSource(sell_rule_id=safe_rule_id))
        return self._set_cleanup_protection_sources(existing_sources)

    def _get_sell_rule_by_id(self, sell_rule_id: object) -> SellRule | None:
        safe_rule_id = _normalize_rule_id(sell_rule_id)
        if not safe_rule_id:
            return None
        for sell_rule in self.sell_rules:
            normalized_rule = _normalize_sell_rule(sell_rule)
            if normalized_rule is None:
                continue
            if str(normalized_rule.rule_id or "").strip() == safe_rule_id:
                return normalized_rule
        return None

    def _get_sell_rule_index_by_id(self, sell_rule_id: object) -> int:
        safe_rule_id = _normalize_rule_id(sell_rule_id)
        if not safe_rule_id:
            return -1
        for index, sell_rule in enumerate(self.sell_rules):
            normalized_rule = _normalize_sell_rule(sell_rule)
            if normalized_rule is None:
                continue
            if str(normalized_rule.rule_id or "").strip() == safe_rule_id:
                return index
        return -1

    def _get_cleanup_linkable_sell_rules(self) -> list[SellRule]:
        linkable_rules: list[SellRule] = []
        for sell_rule in self.sell_rules:
            normalized_rule = _normalize_sell_rule(sell_rule)
            if normalized_rule is None:
                continue
            if normalized_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                continue
            linkable_rules.append(normalized_rule)
        return linkable_rules

    def _set_sell_rule_blacklist_model_ids(self, rule: SellRule, model_ids: list[int]) -> bool:
        normalized_ids = _dedupe_model_ids(model_ids)
        if normalized_ids == rule.blacklist_model_ids:
            return False
        rule.blacklist_model_ids = normalized_ids
        return True

    def _set_sell_rule_blacklist_item_type_ids(self, rule: SellRule, item_type_ids: list[object]) -> bool:
        normalized_ids = _dedupe_weapon_item_type_ids(item_type_ids)
        if normalized_ids == rule.blacklist_item_type_ids:
            return False
        rule.blacklist_item_type_ids = normalized_ids
        return True

    def _get_weapon_item_type_label(self, item_type_id: int) -> str:
        return WEAPON_ITEM_TYPE_NAMES.get(int(item_type_id), f"ItemType {int(item_type_id)}")

    def _set_sell_rule_weapon_requirement_rules(self, rule: SellRule, requirement_rules: list[object]) -> bool:
        normalized_rules = _normalize_weapon_requirement_rules(requirement_rules)
        if normalized_rules == rule.protected_weapon_requirement_rules:
            return False
        rule.protected_weapon_requirement_rules = normalized_rules
        return True

    def _add_sell_rule_weapon_requirement_rule(
        self,
        rule: SellRule,
        model_id: int,
        *,
        min_requirement: int = 1,
        max_requirement: int = 8,
    ) -> bool:
        safe_model_id = max(0, _safe_int(model_id, 0))
        if safe_model_id <= 0:
            return False
        min_requirement, max_requirement = _normalize_weapon_requirement_range(min_requirement, max_requirement)
        next_rules = list(rule.protected_weapon_requirement_rules)
        next_rules.append(
            WeaponRequirementRule(
                model_id=safe_model_id,
                min_requirement=min_requirement,
                max_requirement=max_requirement,
            )
        )
        return self._set_sell_rule_weapon_requirement_rules(rule, next_rules)

    def _set_sell_rule_weapon_mod_identifiers(self, rule: SellRule, identifiers: list[str]) -> bool:
        normalized_ids = _dedupe_identifiers(identifiers)
        if normalized_ids == rule.protected_weapon_mod_identifiers:
            return False
        rule.protected_weapon_mod_identifiers = normalized_ids
        return True

    def _set_sell_rule_rune_identifiers(self, rule: SellRule, identifiers: list[str]) -> bool:
        normalized_ids = _dedupe_identifiers(identifiers)
        if normalized_ids == rule.protected_rune_identifiers:
            return False
        rule.protected_rune_identifiers = normalized_ids
        return True

    def _move_rule_entry(self, rules: list[object], index: int, delta: int) -> bool:
        target_index = int(index) + int(delta)
        if index < 0 or target_index < 0 or target_index >= len(rules):
            return False
        rules[index], rules[target_index] = rules[target_index], rules[index]
        self.rule_ui_structure_changed = True
        self._refresh_rule_ui_caches()
        return True

    def _get_buy_rule_indices_for_kind(self, kind: str) -> list[int]:
        indices: list[int] = []
        for index, raw_rule in enumerate(self.buy_rules):
            normalized_rule = _normalize_buy_rule(raw_rule)
            if normalized_rule is not None and normalized_rule.kind == kind:
                indices.append(index)
        return indices

    def _get_sell_rule_indices_for_kind(self, kind: str) -> list[int]:
        indices: list[int] = []
        for index, raw_rule in enumerate(self.sell_rules):
            normalized_rule = _normalize_sell_rule(raw_rule)
            if normalized_rule is not None and normalized_rule.kind == kind:
                indices.append(index)
        return indices

    def _get_destroy_rule_indices_for_kind(self, kind: str) -> list[int]:
        indices: list[int] = []
        for index, raw_rule in enumerate(self.destroy_rules):
            normalized_rule = _normalize_destroy_rule(raw_rule)
            if normalized_rule.kind == kind:
                indices.append(index)
        return indices

    def _get_sell_rule_order_within_kind(self, index: int, kind: str) -> int:
        same_kind_indices = self._get_sell_rule_indices_for_kind(kind)
        if index in same_kind_indices:
            return same_kind_indices.index(index) + 1
        return int(index) + 1

    def _draw_add_all_matches_button(self, button_id: str, visible_count: int, addable_count: int) -> bool:
        if visible_count <= 0:
            return False

        PyImGui.begin_disabled(addable_count <= 0)
        clicked = PyImGui.small_button(f"Add All Matches ({visible_count})##{button_id}")
        PyImGui.end_disabled()
        return clicked and addable_count > 0

    def _draw_search_results(self, child_id: str, query: str) -> tuple[int, list[int]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return 0, []

        results = self._search_catalog(normalized_query)
        visible_model_ids = _collect_model_ids_from_catalog_entries(results)
        picked_model_id = 0
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching items found in the local catalog.")
            else:
                for entry in results:
                    model_id = int(entry.get("model_id", 0))
                    label = self._format_model_label_long(model_id)
                    if PyImGui.selectable(f"{label}##{child_id}_{model_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_model_id = model_id
                        break
        PyImGui.end_child()
        return picked_model_id, visible_model_ids

    def _draw_material_search_results(self, child_id: str, query: str) -> tuple[int, list[int]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return 0, []

        results = self._search_material_catalog(normalized_query)
        visible_model_ids = _collect_model_ids_from_catalog_entries(results)
        picked_model_id = 0
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching crafting materials found in the local catalog.")
            else:
                for entry in results:
                    model_id = int(entry.get("model_id", 0))
                    material_type = str(entry.get("material_type", "")).strip().lower()
                    label = self._format_model_label(model_id)
                    if material_type:
                        label = f"{label} [{material_type}]"
                    if PyImGui.selectable(f"{label}##{child_id}_{model_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_model_id = model_id
                        break
        PyImGui.end_child()
        return picked_model_id, visible_model_ids

    def _draw_common_material_search_results(self, child_id: str, query: str) -> tuple[int, list[int]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return 0, []

        results = self._search_common_material_catalog(normalized_query)
        visible_model_ids = _collect_model_ids_from_catalog_entries(results)
        picked_model_id = 0
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching common crafting materials found in the local catalog.")
            else:
                for entry in results:
                    model_id = int(entry.get("model_id", 0))
                    material_type = str(entry.get("material_type", "")).strip().lower()
                    label = self._format_model_label(model_id)
                    if material_type:
                        label = f"{label} [{material_type}]"
                    if PyImGui.selectable(f"{label}##{child_id}_{model_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_model_id = model_id
                        break
        PyImGui.end_child()
        return picked_model_id, visible_model_ids

    def _draw_weapon_search_results(self, child_id: str, query: str) -> tuple[int, list[int]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return 0, []

        results = self._search_weapon_catalog(normalized_query)
        visible_model_ids = _collect_model_ids_from_catalog_entries(results)
        picked_model_id = 0
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching weapon models found in the local catalog.")
            else:
                for entry in results:
                    model_id = int(entry.get("model_id", 0))
                    label = self._format_model_label_long(model_id)
                    if PyImGui.selectable(f"{label}##{child_id}_{model_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_model_id = model_id
                        break
        PyImGui.end_child()
        return picked_model_id, visible_model_ids

    def _draw_blacklist_search_results(
        self,
        child_id: str,
        query: str,
        existing_model_ids: list[int],
        *,
        entry_predicate: Callable[[dict[str, object]], bool] | None = None,
    ) -> tuple[int, dict[str, object] | None, dict[str, int | bool | str], list[int]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return 0, None, {
                "query": "",
                "item_results": 0,
                "alias_groups": 0,
                "catalog_empty": len(self.catalog_by_model_id) <= 0,
            }, []

        alias_groups = self._search_catalog_alias_groups(
            normalized_query,
            exclude_model_ids=existing_model_ids,
            entry_predicate=entry_predicate,
        )
        item_results = (
            self._search_catalog_with_predicate(normalized_query, entry_predicate=entry_predicate)
            if entry_predicate is not None
            else self._search_catalog(normalized_query)
        )
        visible_item_model_ids = _collect_model_ids_from_catalog_entries(item_results)
        picked_model_id = 0
        picked_group_info: dict[str, object] | None = None
        child_height = 140 if len(alias_groups) + len(item_results) > 4 else 100
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not alias_groups and not item_results:
                PyImGui.text_wrapped("No matching items found in the local catalog.")
            else:
                for group in alias_groups:
                    display_name = str(group.get("display_name", "")).strip() or "Matching Variants"
                    group_model_ids = _dedupe_model_ids(list(group.get("model_ids", [])))
                    if len(group_model_ids) < 2:
                        continue
                    label = f"Add all matching variants: {display_name} ({len(group_model_ids)} models)"
                    if PyImGui.selectable(f"{label}##{child_id}_group_{display_name}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_group_info = {
                            "display_name": display_name,
                            "model_ids": group_model_ids,
                        }
                        break

                if picked_group_info is None and alias_groups and item_results:
                    PyImGui.separator()

                if picked_group_info is None:
                    for entry in item_results:
                        model_id = int(entry.get("model_id", 0))
                        label = self._format_model_label_long(model_id)
                        if PyImGui.selectable(f"{label}##{child_id}_{model_id}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                            picked_model_id = model_id
                            break
        PyImGui.end_child()
        return picked_model_id, picked_group_info, {
            "query": normalized_query,
            "item_results": len(item_results),
            "alias_groups": len(alias_groups),
            "catalog_empty": len(self.catalog_by_model_id) <= 0,
        }, visible_item_model_ids

    def _draw_identifier_search_results(self, child_id: str, query: str, entries: list[dict[str, str]]) -> tuple[str, list[str]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return "", []

        results = self._search_identifier_catalog(normalized_query, entries)
        visible_identifiers = _collect_identifiers_from_catalog_entries(results)
        picked_identifier = ""
        child_height = 110 if len(results) > 4 else 80
        if PyImGui.begin_child(child_id, (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not results:
                PyImGui.text_wrapped("No matching modifier entries found.")
            else:
                for entry in results:
                    identifier = str(entry.get("identifier", "")).strip()
                    name = str(entry.get("name", identifier)).strip()
                    if PyImGui.selectable(f"{name}##{child_id}_{identifier}", False, PyImGui.SelectableFlags.NoFlag, (0, 0)):
                        picked_identifier = identifier
                        break
        PyImGui.end_child()
        return picked_identifier, visible_identifiers

    def _draw_selected_model_ids(
        self,
        section_name: str,
        index: int,
        model_ids: list[int],
        *,
        jump_anchor: str = "",
    ) -> int:
        if not model_ids:
            self._draw_secondary_text("No items selected yet.", wrapped=False)
            return 0

        removed_model_id = 0
        child_height = min(150, 28 + (22 * len(model_ids)))
        if PyImGui.begin_child(f"{section_name}_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            for model_id in self._sort_model_ids_for_display(model_ids):
                if PyImGui.small_button(f"X##{section_name}_remove_{index}_{model_id}"):
                    removed_model_id = model_id
                    break
                PyImGui.same_line(0, 6)
                PyImGui.text(self._format_model_label_long(model_id))
                if jump_anchor:
                    self._maybe_scroll_sell_jump_target_row(index, jump_anchor, f"model:{int(model_id)}")
        PyImGui.end_child()
        return removed_model_id

    def _draw_whitelist_targets(
        self,
        *,
        section_name: str,
        index: int,
        targets: list[WhitelistTarget],
        item_column_label: str,
        empty_text: str,
        show_merchant_column: bool = False,
        show_deposit_column: bool = False,
        merchant_label_getter: Callable[[int], str] | None = None,
    ) -> tuple[list[WhitelistTarget], int]:
        normalized_targets = _normalize_whitelist_targets(targets)
        if not normalized_targets:
            self._draw_secondary_text(empty_text, wrapped=False)
            return [], 0

        updated_targets = [
            WhitelistTarget(
                model_id=target.model_id,
                keep_count=target.keep_count,
                deposit_to_storage=bool(getattr(target, "deposit_to_storage", False)),
            )
            for target in normalized_targets
        ]
        display_targets = self._sort_targets_by_model_label_for_display(updated_targets)
        removed_model_id = 0
        column_count = 2
        if show_merchant_column:
            column_count += 1
        if show_deposit_column:
            column_count += 1
        column_count += 1
        child_height = min(220, 58 + (32 * len(updated_targets)))
        if PyImGui.begin_child(f"{section_name}_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table(f"{section_name}_table_{index}", column_count, PyImGui.TableFlags.NoFlag):
                PyImGui.table_setup_column(item_column_label, PyImGui.TableColumnFlags.WidthStretch)
                if show_merchant_column:
                    PyImGui.table_setup_column("Merchant", PyImGui.TableColumnFlags.WidthFixed, 120.0)
                PyImGui.table_setup_column("Keep", PyImGui.TableColumnFlags.WidthFixed, 130.0)
                if show_deposit_column:
                    PyImGui.table_setup_column("Deposit", PyImGui.TableColumnFlags.WidthFixed, 90.0)
                PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(item_column_label)
                if show_merchant_column:
                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Merchant")
                keep_column_index = 1 if not show_merchant_column else 2
                deposit_column_index = keep_column_index + 1 if show_deposit_column else -1
                remove_column_index = keep_column_index + (2 if show_deposit_column else 1)
                PyImGui.table_set_column_index(keep_column_index)
                PyImGui.text("Keep")
                if show_deposit_column:
                    PyImGui.table_set_column_index(deposit_column_index)
                    PyImGui.text("Deposit")
                PyImGui.table_set_column_index(remove_column_index)
                PyImGui.text("Remove")

                for target_row in display_targets:
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(self._format_model_label_short(target_row.model_id))

                    if show_merchant_column:
                        PyImGui.table_set_column_index(1)
                        merchant_label = ""
                        if merchant_label_getter is not None:
                            merchant_label = str(merchant_label_getter(target_row.model_id) or "")
                        PyImGui.text(merchant_label)

                    PyImGui.table_set_column_index(keep_column_index)
                    PyImGui.push_item_width(120)
                    new_keep_count = PyImGui.input_int(
                        f"##{section_name}_keep_{index}_{target_row.model_id}",
                        int(target_row.keep_count),
                    )
                    PyImGui.pop_item_width()
                    target_row.keep_count = max(0, int(new_keep_count))

                    if show_deposit_column:
                        PyImGui.table_set_column_index(deposit_column_index)
                        target_row.deposit_to_storage = PyImGui.checkbox(
                            f"##{section_name}_deposit_{index}_{target_row.model_id}",
                            bool(target_row.deposit_to_storage),
                        )

                    PyImGui.table_set_column_index(remove_column_index)
                    if PyImGui.small_button(f"X##{section_name}_remove_{index}_{target_row.model_id}"):
                        removed_model_id = target_row.model_id
                        break

                PyImGui.end_table()
        PyImGui.end_child()
        return updated_targets, removed_model_id

    def _draw_selected_identifiers(
        self,
        section_name: str,
        index: int,
        identifiers: list[str],
        formatter,
        *,
        jump_anchor: str = "",
    ) -> str:
        if not identifiers:
            self._draw_secondary_text("No protected entries selected yet.", wrapped=False)
            return ""

        removed_identifier = ""
        child_height = min(150, 28 + (22 * len(identifiers)))
        if PyImGui.begin_child(f"{section_name}_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            for identifier in self._sort_identifiers_for_display(identifiers, formatter):
                if PyImGui.small_button(f"X##{section_name}_remove_{index}_{identifier}"):
                    removed_identifier = identifier
                    break
                PyImGui.same_line(0, 6)
                PyImGui.text(str(formatter(identifier)))
                if jump_anchor:
                    self._maybe_scroll_sell_jump_target_row(index, jump_anchor, f"identifier:{str(identifier)}")
        PyImGui.end_child()
        return removed_identifier

    def _resolve_rune_trader_coords(self, map_id: int, *, log_failures: bool = True) -> tuple[float, float] | None:
        selector_name = str(SUPPORTED_MAP_RUNE_TRADER_SELECTORS.get(int(map_id), "") or "").strip()
        if selector_name:
            step = {"npc": selector_name}
        else:
            step = {"target": RUNE_TRADER_NAME_QUERY}
        return resolve_agent_xy_from_step(
            step,
            recipe_name=MODULE_NAME,
            step_idx=0,
            agent_kind="npc",
            default_max_dist=OUTPOST_SERVICE_SEARCH_MAX_DIST,
            log_failures=log_failures,
        )

    def _resolve_service_coords(
        self,
        *,
        selector_name: str = "",
        name_query: str = "",
        log_failures: bool = True,
    ) -> tuple[float, float] | None:
        lookup_steps: list[dict[str, object]] = []
        safe_selector_name = str(selector_name or "").strip()
        safe_name_query = str(name_query or "").strip()
        if safe_selector_name:
            lookup_steps.append({"npc": safe_selector_name})
        if safe_name_query:
            lookup_steps.append({"target": safe_name_query})
        if not lookup_steps:
            return None

        last_lookup_index = len(lookup_steps) - 1
        for lookup_index, step in enumerate(lookup_steps):
            coords = resolve_agent_xy_from_step(
                step,
                recipe_name=MODULE_NAME,
                step_idx=lookup_index,
                agent_kind="npc",
                default_max_dist=OUTPOST_SERVICE_SEARCH_MAX_DIST,
                log_failures=bool(log_failures and lookup_index == last_lookup_index),
            )
            if coords is not None:
                return coords
        return None

    def _resolve_storage_access_coords(self) -> tuple[float, float] | None:
        if not Map.IsMapReady():
            return None
        if not Map.IsOutpost() and not Map.IsGuildHall():
            return None

        lookup_steps: list[tuple[dict[str, object], str]] = [
            ({"target": XUNLAI_AGENT_NAME_QUERY, "exact_name": True}, "npc"),
            ({"target": XUNLAI_CHEST_NAME_QUERY, "exact_name": True}, "gadget"),
        ]
        lookup_steps.extend(({"model_id": model_id}, "npc") for model_id in XUNLAI_AGENT_MODEL_IDS)
        lookup_steps.append(({"model_id": XUNLAI_CHEST_MODEL_ID}, "gadget"))

        for step, agent_kind in lookup_steps:
            coords = resolve_agent_xy_from_step(
                step,
                recipe_name=MODULE_NAME,
                step_idx=0,
                agent_kind=agent_kind,
                default_max_dist=OUTPOST_SERVICE_SEARCH_MAX_DIST,
                log_failures=False,
            )
            if coords is not None:
                return coords
        return None

    def _has_local_storage_access(self) -> bool:
        storage_api = getattr(GLOBAL_CACHE, "Inventory", None)
        if storage_api is not None:
            try:
                if bool(getattr(storage_api, "IsStorageOpen", lambda: False)()):
                    return True
            except Exception:
                pass
        return self._resolve_storage_access_coords() is not None

    def _load_profile(self):
        profile_exists = os.path.exists(self.config_path)
        self.new_profile_session = not profile_exists
        self.active_workspace = WORKSPACE_RULES if self.new_profile_session else WORKSPACE_OVERVIEW
        self.active_rules_workspace = RULES_WORKSPACE_BUY
        self.profile_warning = ""
        self.profile_notice = ""

        default_payload = {
            "version": PROFILE_VERSION,
            "auto_cleanup_on_outpost_entry": False,
            "auto_travel_enabled": False,
            "target_outpost_id": 0,
            "favorite_outpost_ids": [],
            "debug_logging": False,
            "window_x": None,
            "window_y": None,
            "window_width": 0,
            "window_height": 0,
            "window_collapsed": False,
            "buy_rules": [asdict(rule) for rule in (_default_buy_rules() if profile_exists else [])],
            "sell_rules": [asdict(rule) for rule in (_default_sell_rules() if profile_exists else [])],
            "destroy_rules": [asdict(rule) for rule in (_default_destroy_rules() if profile_exists else [])],
            "cleanup_targets": [],
            "cleanup_protection_sources": [],
        }
        self._apply_profile_payload(default_payload)

        if not profile_exists:
            return

        should_save_normalized = False
        allow_normalized_save = True
        raw_version = 0
        normalized_payload: dict[str, object] | None = None
        try:
            raw_payload = self._load_profile_from_path(self.config_path)
            raw_version = _safe_int(raw_payload.get("version", 0), 0) if isinstance(raw_payload, dict) else 0
            if raw_version > PROFILE_VERSION:
                allow_normalized_save = False
                self.profile_warning = (
                    f"Live config version {raw_version} is newer than Merchant Rules version {PROFILE_VERSION}. "
                    f"Loaded in compatibility mode without rewriting the file."
                )
            normalized_payload = self._normalize_profile_payload(raw_payload)
            should_save_normalized = self._serialize_profile_payload(raw_payload) != self._serialize_profile_payload(normalized_payload)
            self._apply_profile_payload(normalized_payload)
        except Exception as exc:
            backup_path = ""
            try:
                backup_path = self._snapshot_failed_profile(self.config_path)
            except Exception as backup_exc:
                ConsoleLog(MODULE_NAME, f"Failed to snapshot unreadable live config {self.config_path}: {backup_exc}", Console.MessageType.Warning)
            backup_label = os.path.basename(backup_path) if backup_path else "no recovery backup was created"
            self.profile_warning = (
                f"Live config load failed; using in-memory defaults and preserving the original file. Backup: {backup_label}."
            )
            self.active_workspace = WORKSPACE_RULES
            ConsoleLog(MODULE_NAME, f"Failed to load live config {self.config_path}: {exc}", Console.MessageType.Error)
            return

        if raw_version <= 0 and not self.profile_warning:
            self.profile_notice = "Loaded a legacy live config without a version marker."
        elif 0 < raw_version < PROFILE_VERSION and not self.profile_warning:
            self.profile_notice = f"Loaded and normalized Merchant Rules live config v{raw_version}."

        if should_save_normalized and allow_normalized_save and normalized_payload is not None:
            if self._save_profile():
                if raw_version <= 0:
                    self.profile_notice = f"Legacy live config normalized and saved safely to v{PROFILE_VERSION}."
                elif raw_version < PROFILE_VERSION:
                    self.profile_notice = f"Live config migrated from v{raw_version} to v{PROFILE_VERSION} and saved safely."
                else:
                    self.profile_notice = "Live config normalized and saved safely."

    def _save_profile(self) -> bool:
        saved_window_geometry = bool(self.window_geometry_dirty)
        payload = self._build_profile_payload()
        try:
            self._write_profile_payload_to_path(
                self.config_path,
                payload,
                backup_mode="recovery",
            )
            if saved_window_geometry:
                self.window_geometry_dirty = False
                self.window_geometry_save_timer.Reset()
            return True
        except Exception as exc:
            self.profile_warning = f"Failed to save Merchant Rules live config safely: {exc}"
            ConsoleLog(MODULE_NAME, f"Failed to save live config {self.config_path}: {exc}", Console.MessageType.Error)
            return False

    def _mark_preview_dirty(self, message: str = ""):
        self.preview_ready = False
        self._clear_preview_projection_state()
        self._clear_preview_inventory_diff()
        if message:
            self.status_message = message

    def _apply_window_geometry(self):
        if self.window_geometry_needs_apply:
            if self.window_x is not None and self.window_y is not None:
                PyImGui.set_next_window_pos(float(self.window_x), float(self.window_y))
            if self.window_width > 0 and self.window_height > 0:
                PyImGui.set_next_window_size(float(self.window_width), float(self.window_height))
            else:
                PyImGui.set_next_window_size(float(DEFAULT_WINDOW_WIDTH), float(DEFAULT_WINDOW_HEIGHT))
            PyImGui.set_next_window_collapsed(bool(self.window_collapsed), 0)
            self.window_geometry_needs_apply = False

    def _track_window_geometry(self, window_expanded: bool):
        end_pos = PyImGui.get_window_pos()
        end_size = PyImGui.get_window_size()
        new_collapsed = bool(PyImGui.is_window_collapsed())

        next_x = int(end_pos[0]) if isinstance(end_pos, (tuple, list)) and len(end_pos) >= 2 else self.window_x
        next_y = int(end_pos[1]) if isinstance(end_pos, (tuple, list)) and len(end_pos) >= 2 else self.window_y
        next_width = self.window_width
        next_height = self.window_height
        if window_expanded and isinstance(end_size, (tuple, list)) and len(end_size) >= 2:
            next_width = max(0, int(end_size[0]))
            next_height = max(0, int(end_size[1]))

        changed = False
        if next_x != self.window_x or next_y != self.window_y:
            self.window_x = next_x
            self.window_y = next_y
            changed = True
        if next_width != self.window_width or next_height != self.window_height:
            self.window_width = next_width
            self.window_height = next_height
            changed = True
        if new_collapsed != self.window_collapsed:
            self.window_collapsed = new_collapsed
            changed = True

        if changed:
            self.window_geometry_dirty = True

        if self.window_geometry_dirty and self.window_geometry_save_timer.IsExpired():
            self._save_profile()
            self.window_geometry_dirty = False
            self.window_geometry_save_timer.Reset()

    def _get_supported_context(self, *, passive: bool = False) -> tuple[bool, str, dict[str, tuple[float, float] | None]]:
        current_map_id = int(Map.GetMapID() or 0)
        if self.cached_supported_context is not None and self.cached_context_map_id == current_map_id:
            return self.cached_supported_context

        coords: dict[str, tuple[float, float] | None] = {
            MERCHANT_TYPE_MERCHANT: None,
            MERCHANT_TYPE_MATERIALS: None,
            MERCHANT_TYPE_RUNE_TRADER: None,
            MERCHANT_TYPE_RARE_MATERIALS: None,
        }

        if not Map.IsMapReady():
            self.cached_context_map_id = current_map_id
            self.cached_supported_context = (False, "Map is not ready.", coords)
            return self.cached_supported_context
        if not Map.IsOutpost() and not Map.IsGuildHall():
            self.cached_context_map_id = current_map_id
            self.cached_supported_context = (False, "Current map is not an outpost or Guild Hall.", coords)
            return self.cached_supported_context

        map_id = current_map_id
        selector_data = SUPPORTED_MAP_NPC_SELECTORS.get(map_id)
        if selector_data is None:
            selector_data = {}

        selector_keys = {
            MERCHANT_TYPE_MERCHANT: ("merchant", MERCHANT_NAME_QUERY),
            MERCHANT_TYPE_MATERIALS: ("materials", MATERIAL_TRADER_NAME_QUERY),
            MERCHANT_TYPE_RARE_MATERIALS: ("rare_materials", RARE_MATERIAL_TRADER_NAME_QUERY),
        }

        for merchant_type, (selector_key, name_query) in selector_keys.items():
            selector_name = selector_data.get(selector_key) or DEFAULT_NPC_SELECTORS.get(selector_key)
            if not selector_name and not name_query:
                continue
            coords[merchant_type] = self._resolve_service_coords(
                selector_name=str(selector_name or ""),
                name_query=name_query,
                log_failures=not passive,
            )

        coords[MERCHANT_TYPE_RUNE_TRADER] = self._resolve_rune_trader_coords(map_id, log_failures=not passive)

        resolved_count = sum(1 for value in coords.values() if value is not None)
        location_label = "Guild Hall" if Map.IsGuildHall() else "Outpost"
        base_message = (
            f"{location_label} ready: {Map.GetMapName(map_id)} ({map_id}). Using specific merchant selectors."
            if map_id in SUPPORTED_MAP_NPC_SELECTORS
            else f"{location_label} ready: {Map.GetMapName(map_id)} ({map_id}). Using generic merchant selectors."
        )
        if resolved_count <= 0:
            supported_map = False
            reason = f"{base_message} No merchant or trader selectors resolved."
        elif resolved_count < len(coords):
            supported_map = True
            reason = f"{base_message} Partial merchant/trader resolution succeeded."
        else:
            supported_map = True
            reason = f"{base_message} Merchant, material trader, rune trader, and rare material trader resolved."

        self.cached_context_map_id = current_map_id
        self.cached_supported_context = (supported_map, reason, coords)
        selector_mode = "specific" if map_id in SUPPORTED_MAP_NPC_SELECTORS else "generic"
        self._debug_log(
            f"Context resolved: map={Map.GetMapName(map_id)} ({map_id}) selector_mode={selector_mode} "
            f"supported={supported_map} merchant={self._format_debug_coords(coords[MERCHANT_TYPE_MERCHANT])} "
            f"materials={self._format_debug_coords(coords[MERCHANT_TYPE_MATERIALS])} "
            f"rune={self._format_debug_coords(coords[MERCHANT_TYPE_RUNE_TRADER])} "
            f"rare={self._format_debug_coords(coords[MERCHANT_TYPE_RARE_MATERIALS])}"
        )
        if not supported_map or resolved_count < len(coords):
            self._debug_log(f"Context detail: {reason}")
        return self.cached_supported_context

    def _get_projected_supported_context(self, target_outpost_id: int) -> tuple[bool, str, dict[str, tuple[float, float] | None]]:
        safe_outpost_id = max(0, _safe_int(target_outpost_id, 0))
        outpost_name = self._get_outpost_name(safe_outpost_id)
        coords: dict[str, tuple[float, float] | None] = {
            MERCHANT_TYPE_MERCHANT: PROJECTED_PREVIEW_CONTEXT_COORDS,
            MERCHANT_TYPE_MATERIALS: PROJECTED_PREVIEW_CONTEXT_COORDS,
            MERCHANT_TYPE_RUNE_TRADER: PROJECTED_PREVIEW_CONTEXT_COORDS,
            MERCHANT_TYPE_RARE_MATERIALS: PROJECTED_PREVIEW_CONTEXT_COORDS,
        }
        if safe_outpost_id <= 0 or not outpost_name:
            return False, "Projected preview target is not configured.", {
                MERCHANT_TYPE_MERCHANT: None,
                MERCHANT_TYPE_MATERIALS: None,
                MERCHANT_TYPE_RUNE_TRADER: None,
                MERCHANT_TYPE_RARE_MATERIALS: None,
            }

        selector_mode = "specific merchant selectors" if safe_outpost_id in SUPPORTED_MAP_NPC_SELECTORS else "generic merchant selectors"
        arrival_label = "Guild Hall arrival" if self._is_guild_hall_target(safe_outpost_id) else "arrival"
        reason = (
            f"Projected preview for {outpost_name} ({safe_outpost_id}). "
            f"Travel + Execute will auto-travel, then rebuild live merchant handling after {arrival_label} using {selector_mode}. "
            "Destination NPC and storage access will be confirmed on arrival."
        )
        return True, reason, coords

    def _is_projected_destination_entry(self, entry: ExecutionPlanEntry) -> bool:
        action_type = str(entry.action_type)
        merchant_type = str(entry.merchant_type)
        if merchant_type in (
            MERCHANT_TYPE_MERCHANT,
            MERCHANT_TYPE_MATERIALS,
            MERCHANT_TYPE_RUNE_TRADER,
            MERCHANT_TYPE_RARE_MATERIALS,
        ):
            return action_type in {"buy", "sell"}
        if merchant_type == MERCHANT_TYPE_STORAGE:
            return action_type in {"deposit", "withdraw"}
        return False

    def _get_projected_preview_reason_suffix(self, merchant_type: str, target_outpost_name: str) -> str:
        target_label = str(target_outpost_name or "").strip() or "the selected outpost"
        if str(merchant_type) == MERCHANT_TYPE_STORAGE:
            return f"Projected after travel to {target_label}. Travel + Execute will reopen Xunlai after arrival."
        merchant_label = MERCHANT_TYPE_LABELS.get(str(merchant_type), "merchant handling")
        return (
            f"Projected after travel to {target_label}. "
            f"Travel + Execute will confirm live {merchant_label} access on arrival."
        )

    def _append_projected_preview_reason(self, reason: str, merchant_type: str, target_outpost_name: str) -> str:
        suffix = self._get_projected_preview_reason_suffix(merchant_type, target_outpost_name)
        normalized_reason = str(reason or "").strip()
        if suffix and suffix in normalized_reason:
            return normalized_reason
        if not normalized_reason:
            return suffix
        return f"{normalized_reason} {suffix}".strip()

    def _apply_projected_preview_post_processing(self, plan: PlanResult, target_outpost_name: str):
        for entry in plan.entries:
            if not self._is_projected_destination_entry(entry):
                continue
            if str(entry.state) == PLAN_STATE_WILL_EXECUTE:
                entry.state = PLAN_STATE_CONDITIONAL
            if str(entry.state) == PLAN_STATE_CONDITIONAL:
                entry.reason = self._append_projected_preview_reason(entry.reason, entry.merchant_type, target_outpost_name)

    def _build_travel_preview(self, target_outpost_id: int) -> PlanResult:
        safe_outpost_id = max(0, _safe_int(target_outpost_id, 0))
        outpost_name = self._get_outpost_name(safe_outpost_id)
        if safe_outpost_id <= 0 or not outpost_name:
            return PlanResult(
                supported_map=False,
                supported_reason="Auto-travel target is not configured.",
                has_actions=False,
            )

        is_guild_hall_target = self._is_guild_hall_target(safe_outpost_id)
        selector_mode = "specific selectors" if safe_outpost_id in SUPPORTED_MAP_NPC_SELECTORS else "generic selectors"
        arrival_label = "Guild Hall arrival" if is_guild_hall_target else "arrival"
        travel_reason = (
            f"Travel to Guild Hall first, then rebuild the merchant plan in {selector_mode}."
            if is_guild_hall_target
            else f"Travel first, then rebuild the merchant plan in {selector_mode}."
        )
        result = PlanResult(
            supported_map=True,
            supported_reason=(
                f"Previewing travel to {outpost_name} ({safe_outpost_id}). "
                f"Merchant actions will be re-planned after {arrival_label} using {selector_mode}."
            ),
            travel_to_outpost_id=safe_outpost_id,
            travel_to_outpost_name=outpost_name,
            has_actions=True,
        )
        result.entries.append(
            ExecutionPlanEntry(
                action_type="travel",
                merchant_type=MERCHANT_TYPE_TRAVEL,
                label=outpost_name,
                quantity=1,
                state=PLAN_STATE_WILL_EXECUTE,
                reason=travel_reason,
            )
            )
        return result

    def _get_bag_item_ids(self, bag_ids: tuple[int, ...] | list[int]) -> list[int]:
        normalized_bag_ids = tuple(
            int(bag_id)
            for bag_id in bag_ids
            if max(0, _safe_int(bag_id, 0)) > 0
        )
        if not normalized_bag_ids:
            return []
        bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(*normalized_bag_ids)
        return [int(item_id) for item_id in GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)]

    def _get_inventory_item_ids(self) -> list[int]:
        return self._get_bag_item_ids(list(INVENTORY_BAG_IDS))

    def _is_storage_open(self) -> bool:
        storage_api = getattr(GLOBAL_CACHE, "Inventory", None)
        if storage_api is None:
            return False
        try:
            return bool(getattr(storage_api, "IsStorageOpen", lambda: False)())
        except Exception:
            return False

    def _get_storage_item_ids(self) -> list[int]:
        if not self._is_storage_open():
            return []
        return self._get_bag_item_ids(list(range(8, 22)))

    def _get_item_modifier_values(self, item_id: int) -> tuple[tuple[int, int, int], ...]:
        return tuple(
            (int(modifier.GetIdentifier()), int(modifier.GetArg1()), int(modifier.GetArg2()))
            for modifier in GLOBAL_CACHE.Item.Customization.Modifiers.GetModifiers(item_id)
            if modifier is not None
        )

    def _classify_inventory_item_type(self, item_id: int, item_type_enum: ItemType) -> tuple[bool, bool, ItemType]:
        is_weapon_like = bool(item_type_enum in WEAPON_LIKE_ITEM_TYPES)
        is_armor_piece = bool(GLOBAL_CACHE.Item.Type.IsArmor(item_id) or item_type_enum in ARMOR_PIECE_TYPES)
        parse_item_type = item_type_enum
        if is_armor_piece and parse_item_type not in ARMOR_PIECE_TYPES:
            parse_item_type = ItemType.Chestpiece
        return is_weapon_like, is_armor_piece, parse_item_type

    def _get_cached_inventory_modifiers(
        self,
        item_id: int,
        model_id: int,
        item_type_enum: ItemType,
        parse_item_type: ItemType,
        *,
        is_weapon_like: bool,
        is_armor_piece: bool,
    ) -> ParsedInventoryModifiers:
        if not (is_weapon_like or is_armor_piece or item_type_enum == ItemType.Rune_Mod):
            return ParsedInventoryModifiers()

        raw_modifiers = self._get_item_modifier_values(item_id)
        signature = (
            int(model_id),
            int(getattr(item_type_enum, "value", 0)),
            int(getattr(parse_item_type, "value", 0)),
            raw_modifiers,
        )
        cached_entry = self.inventory_modifier_cache.get(item_id)
        if cached_entry is not None and cached_entry.signature == signature:
            self.inventory_modifier_cache_hits += 1
            return cached_entry.parsed

        self.inventory_modifier_cache_misses += 1
        parsed_state = ParsedInventoryModifiers()
        if raw_modifiers:
            parsed_modifiers = parse_modifiers(list(raw_modifiers), parse_item_type, model_id, MOD_DB)
            rune_identifiers = tuple(_dedupe_identifiers([match.rune.identifier for match in parsed_modifiers.runes]))
            weapon_mod_identifiers = tuple(_dedupe_identifiers([match.weapon_mod.identifier for match in parsed_modifiers.weapon_mods]))
            standalone_kind = ""
            if item_type_enum == ItemType.Rune_Mod:
                if parsed_modifiers.is_rune or rune_identifiers:
                    standalone_kind = RUNE_STANDALONE_KIND
                elif weapon_mod_identifiers:
                    standalone_kind = WEAPON_MOD_STANDALONE_KIND
            parsed_state = ParsedInventoryModifiers(
                requirement=_normalize_weapon_requirement_level(parsed_modifiers.requirements),
                standalone_kind=standalone_kind,
                rune_identifiers=rune_identifiers,
                weapon_mod_identifiers=weapon_mod_identifiers,
            )

        self.inventory_modifier_cache[item_id] = InventoryModifierCacheEntry(
            signature=signature,
            parsed=parsed_state,
        )
        return parsed_state

    def _build_inventory_item_info(self, item_id: int) -> InventoryItemInfo | None:
        try:
            safe_item_id = int(item_id)
            model_id = int(GLOBAL_CACHE.Item.GetModelID(safe_item_id))
            quantity = max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(safe_item_id)))
            value = max(0, int(GLOBAL_CACHE.Item.Properties.GetValue(safe_item_id)))
            item_type_id, item_type_name = GLOBAL_CACHE.Item.GetItemType(safe_item_id)
            try:
                item_type_enum = ItemType(int(item_type_id))
            except Exception:
                item_type_enum = ItemType.Unknown
            _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(safe_item_id)
            is_weapon_like, is_armor_piece, parse_item_type = self._classify_inventory_item_type(safe_item_id, item_type_enum)
            parsed_modifiers = self._get_cached_inventory_modifiers(
                safe_item_id,
                model_id,
                item_type_enum,
                parse_item_type,
                is_weapon_like=is_weapon_like,
                is_armor_piece=is_armor_piece,
            )
            return InventoryItemInfo(
                item_id=safe_item_id,
                model_id=model_id,
                name=str(GLOBAL_CACHE.Item.GetName(safe_item_id) or f"Model {model_id}"),
                quantity=quantity,
                value=value,
                item_type_id=int(item_type_id),
                item_type_name=str(item_type_name or ""),
                rarity=str(rarity or ""),
                identified=bool(GLOBAL_CACHE.Item.Usage.IsIdentified(safe_item_id)),
                salvageable=bool(GLOBAL_CACHE.Item.Usage.IsSalvageable(safe_item_id)),
                is_customized=bool(GLOBAL_CACHE.Item.Properties.IsCustomized(safe_item_id)),
                is_inscribable=bool(GLOBAL_CACHE.Item.Customization.IsInscribable(safe_item_id)),
                is_material=bool(GLOBAL_CACHE.Item.Type.IsMaterial(safe_item_id)),
                is_rare_material=bool(GLOBAL_CACHE.Item.Type.IsRareMaterial(safe_item_id)),
                is_weapon_like=is_weapon_like,
                is_armor_piece=is_armor_piece,
                requirement=int(parsed_modifiers.requirement),
                standalone_kind=str(parsed_modifiers.standalone_kind or ""),
                rune_identifiers=list(parsed_modifiers.rune_identifiers),
                weapon_mod_identifiers=list(parsed_modifiers.weapon_mod_identifiers),
            )
        except Exception:
            return None

    def _prune_inventory_modifier_cache(self, active_item_ids: set[int]):
        stale_item_ids = [item_id for item_id in self.inventory_modifier_cache.keys() if item_id not in active_item_ids]
        for stale_item_id in stale_item_ids:
            self.inventory_modifier_cache.pop(stale_item_id, None)

    def _collect_item_infos_from_ids(self, item_ids: list[int]) -> list[InventoryItemInfo]:
        items: list[InventoryItemInfo] = []
        for item_id in item_ids:
            item_info = self._build_inventory_item_info(item_id)
            if item_info is None:
                continue
            items.append(item_info)
        return items

    def _collect_inventory_items(self) -> list[InventoryItemInfo]:
        started_at = time.perf_counter()
        items = self._collect_item_infos_from_ids(self._get_inventory_item_ids())
        active_item_ids = {
            int(item.item_id)
            for item in items
            if int(item.item_id) > 0
        }
        self._prune_inventory_modifier_cache(active_item_ids)
        self.last_inventory_snapshot_duration_ms = max(0.0, (time.perf_counter() - started_at) * 1000.0)
        if items:
            material_count = sum(1 for item in items if item.is_material and not item.is_rare_material)
            rare_material_count = sum(1 for item in items if item.is_rare_material)
            weapon_count = sum(1 for item in items if item.is_weapon_like)
            armor_count = sum(1 for item in items if item.is_armor_piece)
            standalone_runes = sum(1 for item in items if item.standalone_kind == RUNE_STANDALONE_KIND)
            standalone_weapon_mods = sum(1 for item in items if item.standalone_kind == WEAPON_MOD_STANDALONE_KIND)
            unidentified_count = sum(1 for item in items if not item.identified)
            customized_count = sum(1 for item in items if item.is_customized)
            self._debug_log(
                "Inventory snapshot: "
                f"items={len(items)} materials={material_count} rare_materials={rare_material_count} "
                f"weapons={weapon_count} armor={armor_count} standalone_runes={standalone_runes} "
                f"standalone_weapon_mods={standalone_weapon_mods} unidentified={unidentified_count} "
                f"customized={customized_count} duration_ms={self.last_inventory_snapshot_duration_ms:.2f}"
            )
        else:
            self._debug_log(
                f"Inventory snapshot: no items found in bags 1-4. duration_ms={self.last_inventory_snapshot_duration_ms:.2f}"
            )
        return items

    def _collect_storage_items(self) -> list[InventoryItemInfo]:
        if not self._is_storage_open():
            return []
        return self._collect_item_infos_from_ids(self._get_storage_item_ids())

    def _get_standalone_rune_identifier_counts(self, items: list[InventoryItemInfo]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            if item.standalone_kind != RUNE_STANDALONE_KIND:
                continue
            for identifier in item.rune_identifiers:
                safe_identifier = _normalize_rune_identifier(identifier)
                if not safe_identifier:
                    continue
                counts[safe_identifier] = counts.get(safe_identifier, 0) + max(0, int(item.quantity))
        return counts

    def _get_standalone_rune_identifiers_for_item_id(self, item_id: int) -> tuple[str, ...]:
        item_info = self._build_inventory_item_info(int(item_id))
        if item_info is None or item_info.standalone_kind != RUNE_STANDALONE_KIND:
            return ()
        return tuple(_normalize_rune_identifier(identifier) for identifier in item_info.rune_identifiers if _normalize_rune_identifier(identifier))

    def _get_storage_transfer_items_for_stock_key(
        self,
        storage_items: list[InventoryItemInfo],
        stock_key: str,
        *,
        quantity: int,
        label: str,
        direction: str = STORAGE_TRANSFER_WITHDRAW,
    ) -> list[PlannedStorageTransfer]:
        normalized_quantity = max(0, int(quantity))
        if normalized_quantity <= 0:
            return []

        stock_prefix, stock_value = _parse_stock_key(stock_key)
        matching_items: list[InventoryItemInfo] = []
        if stock_prefix == STOCK_KEY_IDENTIFIER_PREFIX:
            safe_identifier = _normalize_rune_identifier(stock_value)
            matching_items = [
                item
                for item in storage_items
                if item.standalone_kind == RUNE_STANDALONE_KIND and safe_identifier in item.rune_identifiers
            ]
        elif stock_prefix == STOCK_KEY_MODEL_PREFIX:
            safe_model_id = max(0, _safe_int(stock_value, 0))
            matching_items = [item for item in storage_items if int(item.model_id) == safe_model_id]

        transfers: list[PlannedStorageTransfer] = []
        remaining = normalized_quantity
        for item in matching_items:
            if remaining <= 0:
                break
            move_quantity = min(remaining, max(0, int(item.quantity)))
            if move_quantity <= 0:
                continue
            transfers.append(
                PlannedStorageTransfer(
                    direction=direction,
                    key=stock_key,
                    label=label,
                    item_id=int(item.item_id),
                    quantity=move_quantity,
                    model_id=int(item.model_id),
                )
            )
            remaining -= move_quantity
        return transfers

    def _rule_matches_selected_rarity(self, item: InventoryItemInfo, rule: object) -> bool:
        rarity_key = _normalize_rarity_key(item.rarity)
        rule_kind = str(getattr(rule, "kind", ""))
        rule_rarities = getattr(rule, "rarities", {})
        if rule_kind in (SELL_KIND_ARMOR, DESTROY_KIND_ARMOR) and rarity_key == "green":
            return False
        return bool(rule_rarities.get(rarity_key, False))

    def _get_rule_custom_name(self, rule: object) -> str:
        return _normalize_rule_name(getattr(rule, "name", ""))

    def _get_rule_display_label(self, rule: object, default_label: str) -> str:
        custom_name = self._get_rule_custom_name(rule)
        return custom_name or str(default_label or "Rule")

    def _format_rule_reference(self, index: int, default_label: str, custom_name: str = "") -> str:
        normalized_custom_name = _normalize_rule_name(custom_name)
        if normalized_custom_name:
            return f"{normalized_custom_name} (#{int(index) + 1})"
        return f"Rule {int(index) + 1} ({default_label})"

    def _format_buy_rule_reference(self, index: int, rule: BuyRule) -> str:
        return self._format_rule_reference(index, BUY_KIND_LABELS.get(rule.kind, "Buy Rule"), self._get_rule_custom_name(rule))

    def _format_sell_rule_reference(self, index: int, rule: SellRule) -> str:
        return self._format_rule_reference(index, SELL_KIND_LABELS.get(rule.kind, "Sell Rule"), self._get_rule_custom_name(rule))

    def _format_destroy_rule_reference(self, index: int, rule: DestroyRule) -> str:
        return self._format_rule_reference(index, DESTROY_KIND_LABELS.get(rule.kind, "Destroy Rule"), self._get_rule_custom_name(rule))

    def _draw_rule_name_input(self, input_id: str, current_name: str) -> str:
        updated_name = PyImGui.input_text(input_id, _normalize_rule_name(current_name))
        return _normalize_rule_name(updated_name)

    def _get_equippable_rule_destination(self, item: InventoryItemInfo, rule: SellRule) -> str:
        if rule.kind == SELL_KIND_WEAPONS:
            if item.standalone_kind == WEAPON_MOD_STANDALONE_KIND:
                return MERCHANT_TYPE_RUNE_TRADER
            if item.is_weapon_like:
                return MERCHANT_TYPE_MERCHANT
        elif rule.kind == SELL_KIND_ARMOR:
            if rule.include_standalone_runes and item.standalone_kind == RUNE_STANDALONE_KIND:
                return MERCHANT_TYPE_RUNE_TRADER
            if item.is_armor_piece:
                return MERCHANT_TYPE_MERCHANT
        return ""

    def _get_protected_hit_reason(self, item: InventoryItemInfo, rule: SellRule) -> str:
        if rule.kind == SELL_KIND_WEAPONS:
            matched_identifiers = [
                identifier
                for identifier in item.weapon_mod_identifiers
                if identifier in rule.protected_weapon_mod_identifiers
            ]
            if matched_identifiers:
                labels = [self._get_weapon_mod_label(identifier) for identifier in matched_identifiers]
                return f"Contains protected weapon mod: {', '.join(labels)}."

        if rule.kind == SELL_KIND_ARMOR:
            matched_identifiers = [
                identifier
                for identifier in item.rune_identifiers
                if identifier in rule.protected_rune_identifiers
            ]
            if matched_identifiers:
                labels = [self._get_rune_label(identifier) for identifier in matched_identifiers]
                return f"Contains protected rune/insignia: {', '.join(labels)}."

        return ""

    def _get_requirement_rule_item_label(self, item: InventoryItemInfo) -> str:
        catalog_name = str(self._get_model_name(item.model_id) or "").strip()
        if catalog_name:
            return catalog_name
        item_name = str(item.name or "").strip()
        if item_name and item_name.lower() != f"model {int(item.model_id)}".lower():
            return item_name
        return f"Model {int(item.model_id)}"

    def _get_weapon_requirement_hit_reason(self, item: InventoryItemInfo, rule: SellRule) -> str:
        if rule.kind != SELL_KIND_WEAPONS:
            return ""
        if not item.is_weapon_like or item.standalone_kind == WEAPON_MOD_STANDALONE_KIND:
            return ""

        requirement = _normalize_weapon_requirement_level(item.requirement)
        if requirement <= 0:
            return ""

        has_model_requirement_range = False
        for requirement_rule in rule.protected_weapon_requirement_rules:
            if item.model_id != int(requirement_rule.model_id):
                continue
            min_requirement, max_requirement = _normalize_weapon_requirement_range(
                getattr(requirement_rule, "min_requirement", 0),
                getattr(requirement_rule, "max_requirement", 0),
            )
            if not _is_weapon_requirement_range_active(min_requirement, max_requirement):
                continue
            has_model_requirement_range = True
            if min_requirement <= requirement <= max_requirement:
                item_label = self._get_requirement_rule_item_label(item)
                return f"Protected by requirement range: {item_label} req {requirement} in {min_requirement}-{max_requirement}."

        if has_model_requirement_range:
            return ""

        all_weapons_min_requirement, all_weapons_max_requirement = _normalize_weapon_requirement_range(
            getattr(rule, "all_weapons_min_requirement", 0),
            getattr(rule, "all_weapons_max_requirement", 0),
        )
        if (
            _is_weapon_requirement_range_active(all_weapons_min_requirement, all_weapons_max_requirement)
            and all_weapons_min_requirement <= requirement <= all_weapons_max_requirement
        ):
            item_label = self._get_requirement_rule_item_label(item)
            return f"Protected by all-weapons requirement range: {item_label} req {requirement} in {all_weapons_min_requirement}-{all_weapons_max_requirement}."
        return ""

    def _get_equippable_hard_protection_reason(self, item: InventoryItemInfo, rule: SellRule) -> tuple[str, str] | None:
        destination = self._get_equippable_rule_destination(item, rule)
        if not destination:
            return None

        rarity_matches = self._rule_matches_selected_rarity(item, rule)
        if rarity_matches and rule.skip_customized and item.is_customized:
            return destination, "Customized item."
        if rarity_matches and rule.skip_unidentified and not item.identified:
            return destination, "Unidentified item."
        if item.model_id in rule.blacklist_model_ids:
            return destination, "Blacklisted model."
        if rule.kind == SELL_KIND_WEAPONS and item.item_type_id in rule.blacklist_item_type_ids:
            return destination, f"Blacklisted weapon type: {self._get_weapon_item_type_label(item.item_type_id)}."

        requirement_reason = self._get_weapon_requirement_hit_reason(item, rule)
        if requirement_reason:
            return destination, requirement_reason

        protected_reason = self._get_protected_hit_reason(item, rule)
        if protected_reason:
            return destination, protected_reason
        return None

    def _get_equippable_explicit_deposit_reason(self, item: InventoryItemInfo, rule: SellRule) -> tuple[str, str] | None:
        destination = self._get_equippable_rule_destination(item, rule)
        if not destination:
            return None
        if item.model_id in rule.blacklist_model_ids:
            return destination, "Blacklisted model."
        if rule.kind == SELL_KIND_WEAPONS and item.item_type_id in rule.blacklist_item_type_ids:
            return destination, f"Blacklisted weapon type: {self._get_weapon_item_type_label(item.item_type_id)}."

        requirement_reason = self._get_weapon_requirement_hit_reason(item, rule)
        if requirement_reason:
            return destination, requirement_reason

        protected_reason = self._get_protected_hit_reason(item, rule)
        if protected_reason:
            return destination, protected_reason
        return None

    def _get_hard_protection_match(
        self,
        item: InventoryItemInfo,
        enabled_sell_rules: list[tuple[int, SellRule]],
    ) -> tuple[int, SellRule, str, str] | None:
        for rule_index, rule in enabled_sell_rules:
            if rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                continue
            protection = self._get_equippable_hard_protection_reason(item, rule)
            if protection is None:
                continue
            destination, detail = protection
            return rule_index, rule, destination, detail
        return None

    def _get_hard_protection_hit(
        self,
        item: InventoryItemInfo,
        enabled_sell_rules: list[tuple[int, SellRule]],
    ) -> tuple[str, str] | None:
        match = self._get_hard_protection_match(item, enabled_sell_rules)
        if match is not None:
            rule_index, rule, destination, detail = match
            return destination, f"Hard-protected by {self._format_sell_rule_reference(rule_index, rule)}: {detail}"
        return None

    def _can_use_local_storage_actions(self) -> bool:
        return bool(Map.IsMapReady() and (Map.IsOutpost() or Map.IsGuildHall()))

    def _append_storage_transfer_entry(
        self,
        plan: PlanResult,
        *,
        direction: str,
        item_id: int,
        quantity: int,
        label: str,
        reason: str,
        model_id: int = 0,
        key: str = "",
        storage_open: bool = False,
    ) -> None:
        safe_item_id = int(item_id)
        safe_quantity = max(0, int(quantity))
        safe_model_id = max(0, int(model_id))
        if safe_item_id <= 0 or safe_quantity <= 0:
            return
        safe_direction = str(direction)
        action_type = "deposit" if safe_direction == STORAGE_TRANSFER_DEPOSIT else "withdraw"
        default_key = f"item:{safe_item_id}"
        plan.storage_transfers.append(
            PlannedStorageTransfer(
                direction=safe_direction,
                key=str(key or default_key),
                label=str(label or f"Item {safe_item_id}"),
                item_id=safe_item_id,
                quantity=safe_quantity,
                model_id=safe_model_id,
            )
        )
        plan.entries.append(
            ExecutionPlanEntry(
                action_type=action_type,
                merchant_type=MERCHANT_TYPE_STORAGE,
                label=str(label or f"Item {safe_item_id}"),
                quantity=safe_quantity,
                state=PLAN_STATE_WILL_EXECUTE if bool(storage_open) else PLAN_STATE_CONDITIONAL,
                reason=str(reason or ""),
                model_id=safe_model_id,
            )
        )

    def _append_cleanup_transfer_entry(
        self,
        plan: PlanResult,
        *,
        item_id: int,
        quantity: int,
        label: str,
        reason: str,
        model_id: int = 0,
        key: str = "",
        storage_open: bool = False,
    ) -> None:
        safe_item_id = int(item_id)
        safe_quantity = max(0, int(quantity))
        safe_model_id = max(0, int(model_id))
        if safe_item_id <= 0 or safe_quantity <= 0:
            return
        default_key = f"item:{safe_item_id}"
        transfer = PlannedStorageTransfer(
            direction=STORAGE_TRANSFER_DEPOSIT,
            key=str(key or default_key),
            label=str(label or f"Item {safe_item_id}"),
            item_id=safe_item_id,
            quantity=safe_quantity,
            model_id=safe_model_id,
        )
        plan.cleanup_transfers.append(transfer)
        plan.storage_transfers.append(transfer)
        plan.entries.append(
            ExecutionPlanEntry(
                action_type="deposit",
                merchant_type=MERCHANT_TYPE_STORAGE,
                label=str(label or f"Item {safe_item_id}"),
                quantity=safe_quantity,
                state=PLAN_STATE_WILL_EXECUTE if bool(storage_open) else PLAN_STATE_CONDITIONAL,
                reason=str(reason or ""),
                model_id=safe_model_id,
            )
        )

    def _plan_equippable_rule_sales(
        self,
        plan: PlanResult,
        items: list[InventoryItemInfo],
        rule: SellRule,
        rule_index: int,
        claimed_item_ids: set[int],
        coords: dict[str, tuple[float, float] | None],
    ) -> None:
        candidate_label = SELL_KIND_LABELS[rule.kind]
        had_category_candidate = False
        had_rarity_candidate = False
        planned_sale_count = 0
        category_candidates = 0
        rarity_matches = 0
        merchant_sales = 0
        rune_trader_sales = 0
        blocked_matches = 0

        for item in items:
            if item.item_id in claimed_item_ids:
                continue

            destination = self._get_equippable_rule_destination(item, rule)
            if not destination:
                continue

            had_category_candidate = True
            category_candidates += 1
            if not self._rule_matches_selected_rarity(item, rule):
                continue

            had_rarity_candidate = True
            rarity_matches += 1
            if coords.get(destination) is None:
                claimed_item_ids.add(item.item_id)
                blocked_matches += 1
                plan.entries.append(
                    ExecutionPlanEntry(
                        "sell",
                        destination,
                        item.name,
                        item.quantity,
                        "skipped",
                        (
                            f"Blocked by {self._format_sell_rule_reference(rule_index, rule)}: "
                            f"{MERCHANT_TYPE_LABELS[destination]} selector was not resolved in the current map."
                        ),
                        model_id=item.model_id,
                    )
                )
                continue

            claimed_item_ids.add(item.item_id)
            if destination == MERCHANT_TYPE_RUNE_TRADER:
                plan.rune_trader_sales.append(
                    PlannedTraderSale(
                        item_id=item.item_id,
                        model_id=item.model_id,
                        label=item.name,
                    )
                )
            else:
                plan.merchant_sell_item_ids.append(item.item_id)

            reason = "Standalone mod item." if destination == MERCHANT_TYPE_RUNE_TRADER else ""
            plan.entries.append(
                ExecutionPlanEntry(
                    "sell",
                    destination,
                    item.name,
                    item.quantity,
                    "will execute",
                    reason,
                    model_id=item.model_id,
                )
            )
            planned_sale_count += 1
            if destination == MERCHANT_TYPE_RUNE_TRADER:
                rune_trader_sales += 1
            else:
                merchant_sales += 1

        if planned_sale_count > 0 or blocked_matches > 0:
            self._debug_log(
                f"{candidate_label}: category_candidates={category_candidates} rarity_matches={rarity_matches} "
                f"merchant_sales={merchant_sales} rune_trader_sales={rune_trader_sales} "
                f"blocked_matches={blocked_matches}"
            )
            return
        if not had_category_candidate:
            plan.entries.append(
                ExecutionPlanEntry("sell", MERCHANT_TYPE_MERCHANT, candidate_label, 0, "skipped", "No matching inventory items found.")
            )
        elif not had_rarity_candidate:
            plan.entries.append(
                ExecutionPlanEntry("sell", MERCHANT_TYPE_MERCHANT, candidate_label, 0, "skipped", "No matching items found for the enabled rarities.")
            )
        self._debug_log(
            f"{candidate_label}: category_candidates={category_candidates} rarity_matches={rarity_matches} "
            f"merchant_sales={merchant_sales} rune_trader_sales={rune_trader_sales} "
            f"blocked_matches={blocked_matches}"
        )

    def _get_inventory_model_counts(self, items: list[InventoryItemInfo]) -> dict[int, int]:
        counts: dict[int, int] = {}
        for item in items:
            counts[item.model_id] = counts.get(item.model_id, 0) + item.quantity
        return counts

    def _apply_max_per_run(self, needed: int, max_per_run: int) -> int:
        capped_needed = max(0, int(needed))
        cap = max(0, int(max_per_run))
        if cap > 0:
            capped_needed = min(capped_needed, cap)
        return capped_needed

    def _has_enabled_rune_buy_rules(self) -> bool:
        for raw_rule in self.buy_rules:
            rule = _normalize_buy_rule(raw_rule)
            if rule is None or not rule.enabled or rule.kind != BUY_KIND_RUNE_TRADER_TARGET:
                continue
            if _normalize_rune_trader_targets(rule.rune_targets):
                return True
        return False

    def _get_items_after_planned_pre_buy_actions(
        self,
        items: list[InventoryItemInfo],
        plan: PlanResult,
    ) -> list[InventoryItemInfo]:
        remaining_items: list[InventoryItemInfo] = []
        destroy_quantities_by_item_id: dict[int, int] = {}
        material_sale_quantities_by_item_id: dict[int, int] = {}
        merchant_sell_item_ids = {int(item_id) for item_id in plan.merchant_sell_item_ids if int(item_id) > 0}
        rune_sale_item_ids = {
            int(trader_sale.item_id)
            for trader_sale in plan.rune_trader_sales
            if int(trader_sale.item_id) > 0
        }

        if plan.destroy_actions:
            for destroy_action in plan.destroy_actions:
                safe_item_id = int(destroy_action.item_id)
                if safe_item_id <= 0:
                    continue
                destroy_quantities_by_item_id[safe_item_id] = (
                    destroy_quantities_by_item_id.get(safe_item_id, 0)
                    + max(0, int(destroy_action.quantity_to_destroy))
                )
        else:
            for item_id in plan.destroy_item_ids:
                safe_item_id = int(item_id)
                if safe_item_id <= 0:
                    continue
                destroy_quantities_by_item_id[safe_item_id] = max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(safe_item_id)))

        for material_sale in plan.material_sales:
            safe_item_id = int(material_sale.item_id)
            if safe_item_id <= 0:
                continue
            material_sale_quantities_by_item_id[safe_item_id] = (
                material_sale_quantities_by_item_id.get(safe_item_id, 0)
                + max(0, int(material_sale.quantity_to_sell))
            )

        for item in items:
            remaining_quantity = max(0, int(item.quantity))
            if remaining_quantity <= 0:
                continue

            safe_item_id = int(item.item_id)
            remaining_quantity -= max(0, int(destroy_quantities_by_item_id.get(safe_item_id, 0)))
            remaining_quantity -= max(0, int(material_sale_quantities_by_item_id.get(safe_item_id, 0)))
            if safe_item_id in merchant_sell_item_ids or safe_item_id in rune_sale_item_ids:
                remaining_quantity = 0
            if remaining_quantity <= 0:
                continue
            if remaining_quantity == int(item.quantity):
                remaining_items.append(item)
            else:
                remaining_items.append(replace(item, quantity=remaining_quantity))

        return remaining_items

    def _apply_planned_transfer_quantities(
        self,
        items: list[InventoryItemInfo],
        transfers: list[PlannedStorageTransfer],
    ) -> list[InventoryItemInfo]:
        quantity_by_item_id: dict[int, int] = {}
        for transfer in transfers:
            safe_item_id = int(transfer.item_id)
            if safe_item_id <= 0:
                continue
            quantity_by_item_id[safe_item_id] = (
                quantity_by_item_id.get(safe_item_id, 0)
                + max(0, int(transfer.quantity))
            )

        next_items: list[InventoryItemInfo] = []
        for item in items:
            remaining_quantity = max(0, int(item.quantity)) - max(0, int(quantity_by_item_id.get(int(item.item_id), 0)))
            if remaining_quantity <= 0:
                continue
            if remaining_quantity == int(item.quantity):
                next_items.append(item)
            else:
                next_items.append(replace(item, quantity=remaining_quantity))
        return next_items

    def _build_cleanup_target_transfers(
        self,
        matching_items: list[InventoryItemInfo],
        keep_on_character: int,
    ) -> list[PlannedStorageTransfer]:
        normalized_items = [item for item in matching_items if int(item.item_id) > 0 and max(1, int(item.quantity)) > 0]
        safe_keep_count = max(0, int(keep_on_character))
        if not normalized_items:
            return []

        keep_ids, kept_quantity = self._choose_keep_subset_at_most(normalized_items, safe_keep_count)
        remaining_keep_quantity = max(0, safe_keep_count - kept_quantity)
        transfers: list[PlannedStorageTransfer] = []
        for item in normalized_items:
            item_quantity = max(1, int(item.quantity))
            if int(item.item_id) in keep_ids:
                continue

            keep_from_item = 0
            if remaining_keep_quantity > 0:
                keep_from_item = min(item_quantity, remaining_keep_quantity)
                remaining_keep_quantity -= keep_from_item

            transfer_quantity = max(0, item_quantity - keep_from_item)
            if transfer_quantity <= 0:
                continue
            transfers.append(
                PlannedStorageTransfer(
                    direction=STORAGE_TRANSFER_DEPOSIT,
                    key=_make_model_stock_key(item.model_id),
                    label=item.name,
                    item_id=item.item_id,
                    quantity=transfer_quantity,
                    model_id=item.model_id,
                )
            )
        return transfers

    def _get_effective_cleanup_targets(
        self,
        enabled_sell_rules: list[tuple[int, SellRule]] | None = None,
    ) -> list[CleanupTarget]:
        targets_by_model: dict[int, CleanupTarget] = {
            int(target.model_id): CleanupTarget(
                model_id=int(target.model_id),
                keep_on_character=max(0, int(target.keep_on_character)),
            )
            for target in _normalize_cleanup_targets(self.cleanup_targets)
        }
        if enabled_sell_rules is None:
            enabled_sell_rules = self._collect_enabled_sell_rules()
        for _rule_index, sell_rule in enabled_sell_rules:
            if sell_rule.kind not in (SELL_KIND_COMMON_MATERIALS, SELL_KIND_EXPLICIT_MODELS):
                continue
            for whitelist_target in _normalize_whitelist_targets(getattr(sell_rule, "whitelist_targets", [])):
                if not bool(getattr(whitelist_target, "deposit_to_storage", False)):
                    continue
                safe_model_id = max(0, int(whitelist_target.model_id))
                if safe_model_id <= 0 or safe_model_id in targets_by_model:
                    continue
                # Sell-rule keep counts already decide what remains after sales; cleanup deposits that remainder.
                targets_by_model[safe_model_id] = CleanupTarget(model_id=safe_model_id, keep_on_character=0)
        return _normalize_cleanup_targets([asdict(target) for target in targets_by_model.values()])

    def _get_effective_cleanup_protection_sources(
        self,
        enabled_sell_rules: list[tuple[int, SellRule]] | None = None,
    ) -> list[CleanupProtectionSource]:
        sources_by_rule_id: dict[str, CleanupProtectionSource] = {
            str(source.sell_rule_id): CleanupProtectionSource(sell_rule_id=str(source.sell_rule_id))
            for source in _normalize_cleanup_protection_sources(self.cleanup_protection_sources)
        }
        if enabled_sell_rules is None:
            enabled_sell_rules = self._collect_enabled_sell_rules()
        for _rule_index, sell_rule in enabled_sell_rules:
            if sell_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                continue
            if not bool(getattr(sell_rule, "deposit_protected_matches", False)):
                continue
            safe_rule_id = _normalize_rule_id(getattr(sell_rule, "rule_id", ""))
            if not safe_rule_id or safe_rule_id in sources_by_rule_id:
                continue
            sources_by_rule_id[safe_rule_id] = CleanupProtectionSource(sell_rule_id=safe_rule_id)
        return _normalize_cleanup_protection_sources([asdict(source) for source in sources_by_rule_id.values()])

    def _plan_cleanup_actions(
        self,
        plan: PlanResult,
        items: list[InventoryItemInfo],
        enabled_sell_rules: list[tuple[int, SellRule]],
        *,
        storage_open: bool = False,
        storage_context_available: bool | None = None,
    ) -> None:
        if storage_context_available is None:
            storage_context_available = self._can_use_local_storage_actions()
        if not storage_context_available:
            return

        cleanup_items = list(items)
        cleanup_targets = self._get_effective_cleanup_targets(enabled_sell_rules)
        for cleanup_target in cleanup_targets:
            target_model_id = max(0, int(cleanup_target.model_id))
            keep_on_character = max(0, int(cleanup_target.keep_on_character))
            target_label = self._format_model_label(target_model_id)
            matching_items = [
                item
                for item in cleanup_items
                if int(item.model_id) == target_model_id and int(item.item_id) > 0
            ]
            if not matching_items:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        target_label,
                        0,
                        PLAN_STATE_SKIPPED,
                        "No matching inventory items found for this cleanup target.",
                    )
                )
                continue

            total_quantity = sum(max(1, int(item.quantity)) for item in matching_items)
            if total_quantity <= keep_on_character:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        target_label,
                        0,
                        PLAN_STATE_SKIPPED,
                        f"Cleanup reserve keeps {keep_on_character} on character.",
                    )
                )
                continue

            planned_transfers = self._build_cleanup_target_transfers(matching_items, keep_on_character)
            if not planned_transfers:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        target_label,
                        0,
                        PLAN_STATE_SKIPPED,
                        "Cleanup reserve left nothing eligible to move.",
                    )
                )
                continue

            for transfer in planned_transfers:
                self._append_cleanup_transfer_entry(
                    plan,
                    item_id=transfer.item_id,
                    quantity=transfer.quantity,
                    label=transfer.label,
                    model_id=transfer.model_id,
                    key=transfer.key,
                    reason=f"Cleanup target keeps {keep_on_character} on character.",
                    storage_open=storage_open,
                )
            cleanup_items = self._apply_planned_transfer_quantities(cleanup_items, planned_transfers)

        cleanup_sources = self._get_effective_cleanup_protection_sources(enabled_sell_rules)
        for cleanup_source in cleanup_sources:
            sell_rule_id = _normalize_rule_id(cleanup_source.sell_rule_id)
            if not sell_rule_id:
                continue

            sell_rule_index = self._get_sell_rule_index_by_id(sell_rule_id)
            sell_rule = self._get_sell_rule_by_id(sell_rule_id)
            if sell_rule is None or sell_rule_index < 0:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        "Linked protection source",
                        0,
                        PLAN_STATE_SKIPPED,
                        "Linked sell rule no longer exists.",
                    )
                )
                continue

            rule_reference = self._format_sell_rule_reference(sell_rule_index, sell_rule)
            if sell_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        rule_reference,
                        0,
                        PLAN_STATE_SKIPPED,
                        "Linked cleanup sources only support weapon or armor sell protections.",
                    )
                )
                continue

            if not sell_rule.enabled:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        rule_reference,
                        0,
                        PLAN_STATE_SKIPPED,
                        "Linked sell rule is disabled.",
                    )
                )
                continue

            planned_transfers: list[PlannedStorageTransfer] = []
            for item in cleanup_items:
                protection_match = self._get_hard_protection_match(item, enabled_sell_rules)
                if protection_match is None:
                    continue
                _, matched_rule, _, detail = protection_match
                if str(getattr(matched_rule, "rule_id", "") or "").strip() != sell_rule_id:
                    continue
                explicit_deposit = self._get_equippable_explicit_deposit_reason(item, sell_rule)
                if explicit_deposit is None:
                    continue
                planned_transfers.append(
                    PlannedStorageTransfer(
                        direction=STORAGE_TRANSFER_DEPOSIT,
                        key=_make_model_stock_key(item.model_id),
                        label=item.name,
                        item_id=item.item_id,
                        quantity=item.quantity,
                        model_id=item.model_id,
                    )
                )
                self._append_cleanup_transfer_entry(
                    plan,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    label=item.name,
                    model_id=item.model_id,
                    key=_make_model_stock_key(item.model_id),
                    reason=f"Protected by {rule_reference}: {detail}",
                    storage_open=storage_open,
                )

            if not planned_transfers:
                plan.entries.append(
                    ExecutionPlanEntry(
                        "deposit",
                        MERCHANT_TYPE_STORAGE,
                        rule_reference,
                        0,
                        PLAN_STATE_SKIPPED,
                        "No protected inventory items matched this linked cleanup source.",
                    )
                )
                continue

            cleanup_items = self._apply_planned_transfer_quantities(cleanup_items, planned_transfers)

    def _get_stock_count_for_key(
        self,
        stock_key: str,
        model_counts: dict[int, int],
        identifier_counts: dict[str, int],
    ) -> int:
        stock_prefix, stock_value = _parse_stock_key(stock_key)
        if stock_prefix == STOCK_KEY_MODEL_PREFIX:
            return max(0, int(model_counts.get(max(0, _safe_int(stock_value, 0)), 0)))
        if stock_prefix == STOCK_KEY_IDENTIFIER_PREFIX:
            return max(0, int(identifier_counts.get(_normalize_rune_identifier(stock_value), 0)))
        return 0

    def _adjust_stock_count_for_key(
        self,
        stock_key: str,
        delta: int,
        *,
        model_counts: dict[int, int],
        identifier_counts: dict[str, int],
    ) -> None:
        safe_delta = int(delta)
        if safe_delta == 0:
            return

        stock_prefix, stock_value = _parse_stock_key(stock_key)
        if stock_prefix == STOCK_KEY_MODEL_PREFIX:
            model_id = max(0, _safe_int(stock_value, 0))
            if model_id <= 0:
                return
            next_count = max(0, int(model_counts.get(model_id, 0)) + safe_delta)
            if next_count > 0:
                model_counts[model_id] = next_count
            else:
                model_counts.pop(model_id, None)
            return

        if stock_prefix == STOCK_KEY_IDENTIFIER_PREFIX:
            identifier = _normalize_rune_identifier(stock_value)
            if not identifier:
                return
            next_count = max(0, int(identifier_counts.get(identifier, 0)) + safe_delta)
            if next_count > 0:
                identifier_counts[identifier] = next_count
            else:
                identifier_counts.pop(identifier, None)

    def _build_stock_location_counts(
        self,
        stock_key: str,
        label: str,
        *,
        inventory_model_counts: dict[int, int],
        inventory_identifier_counts: dict[str, int],
        storage_model_counts: dict[int, int] | None = None,
        storage_identifier_counts: dict[str, int] | None = None,
        storage_exact: bool = False,
    ) -> StockLocationCounts:
        inventory_count = self._get_stock_count_for_key(
            stock_key,
            inventory_model_counts,
            inventory_identifier_counts,
        )
        storage_count = 0
        if storage_exact:
            storage_count = self._get_stock_count_for_key(
                stock_key,
                storage_model_counts or {},
                storage_identifier_counts or {},
            )
        return StockLocationCounts(
            key=stock_key,
            label=str(label or stock_key),
            inventory_count=inventory_count,
            storage_count=storage_count,
            combined_count=inventory_count + storage_count,
            exact=bool(storage_exact),
        )

    def _has_cleanup_sources(self) -> bool:
        return bool(
            self._get_effective_cleanup_targets()
            or self._get_effective_cleanup_protection_sources()
        )

    def _has_enabled_rules(self) -> bool:
        return (
            any(bool(rule.enabled) for rule in self.buy_rules)
            or any(bool(rule.enabled) for rule in self.sell_rules)
            or any(bool(rule.enabled) for rule in self.destroy_rules)
            or self._has_cleanup_sources()
        )

    def _choose_keep_subset(self, items: list[InventoryItemInfo], keep_count: int) -> set[int]:
        keep_count = max(0, int(keep_count))
        if keep_count <= 0 or not items:
            return set()

        total_quantity = sum(max(1, int(item.quantity)) for item in items)
        if keep_count >= total_quantity:
            return {item.item_id for item in items}

        max_quantity = max(max(1, int(item.quantity)) for item in items)
        sum_cap = min(total_quantity, keep_count + max_quantity)

        parents: dict[int, tuple[int, int] | None] = {0: None}
        for index, item in enumerate(items):
            item_quantity = max(1, int(item.quantity))
            existing_sums = sorted(parents.keys(), reverse=True)
            for current_sum in existing_sums:
                new_sum = current_sum + item_quantity
                if new_sum > sum_cap or new_sum in parents:
                    continue
                parents[new_sum] = (current_sum, index)

        candidate_sums = [value for value in parents.keys() if value >= keep_count]
        if not candidate_sums:
            return {item.item_id for item in items}

        best_sum = min(candidate_sums)
        keep_ids: set[int] = set()
        cursor = best_sum
        while cursor and parents.get(cursor) is not None:
            previous_sum, index = parents[cursor]
            keep_ids.add(items[index].item_id)
            cursor = previous_sum
        return keep_ids

    def _choose_keep_subset_at_most(self, items: list[InventoryItemInfo], keep_count: int) -> tuple[set[int], int]:
        keep_count = max(0, int(keep_count))
        if keep_count <= 0 or not items:
            return set(), 0

        parents: dict[int, tuple[int, int] | None] = {0: None}
        for index, item in enumerate(items):
            item_quantity = max(1, int(item.quantity))
            existing_sums = sorted(parents.keys(), reverse=True)
            for current_sum in existing_sums:
                new_sum = current_sum + item_quantity
                if new_sum > keep_count or new_sum in parents:
                    continue
                parents[new_sum] = (current_sum, index)

        best_sum = max(parents.keys())
        keep_ids: set[int] = set()
        cursor = best_sum
        while cursor and parents.get(cursor) is not None:
            previous_sum, index = parents[cursor]
            keep_ids.add(items[index].item_id)
            cursor = previous_sum
        return keep_ids, best_sum

    def _find_inventory_empty_slot(self, inventory_items: list[InventoryItemInfo] | None = None) -> DestroySplitDestination | None:
        if inventory_items is None:
            inventory_items = self._collect_inventory_items()

        occupied_slots_by_bag: dict[int, set[int]] = {
            int(bag_id): set()
            for bag_id in INVENTORY_BAG_IDS
        }
        for item in inventory_items:
            try:
                bag_id, slot = GLOBAL_CACHE.Inventory.FindItemBagAndSlot(int(item.item_id))
            except Exception:
                continue
            safe_bag_id = int(bag_id or 0)
            safe_slot = int(slot or 0)
            if safe_bag_id not in occupied_slots_by_bag or safe_slot < 0:
                continue
            occupied_slots_by_bag[safe_bag_id].add(safe_slot)

        for bag_id in INVENTORY_BAG_IDS:
            try:
                bag_size = max(0, int(GLOBAL_CACHE.Inventory.GetBagSize(int(bag_id))))
            except Exception:
                bag_size = 0
            if bag_size <= 0:
                continue
            occupied_slots = occupied_slots_by_bag.get(int(bag_id), set())
            for slot in range(bag_size):
                if slot not in occupied_slots:
                    return DestroySplitDestination(bag_id=int(bag_id), slot=int(slot))
        return None

    def _get_destroy_split_block_reason(self, keep_quantity: int) -> str:
        safe_keep_quantity = max(0, int(keep_quantity))
        return (
            f"Keep count requires splitting a stack to preserve {safe_keep_quantity} unit(s), "
            "but no empty inventory slot was available and no earlier destroy action would free one."
        )

    def _plan_stackable_destroy_actions(
        self,
        items: list[InventoryItemInfo],
        keep_count: int,
    ) -> tuple[list[PlannedDestroyAction], dict[int, int], str, int]:
        keep_count = max(0, int(keep_count))
        if not items:
            return [], {}, "", 0

        total_quantity = sum(max(1, int(item.quantity)) for item in items)
        if keep_count >= total_quantity:
            return [], {item.item_id: max(1, int(item.quantity)) for item in items}, "", 0

        whole_keep_ids, kept_total = self._choose_keep_subset_at_most(items, keep_count)
        keep_quantities: dict[int, int] = {
            int(item.item_id): max(1, int(item.quantity))
            for item in items
            if item.item_id in whole_keep_ids
        }

        remaining_keep = max(0, keep_count - kept_total)
        if remaining_keep > 0:
            partial_candidates = [
                item
                for item in items
                if item.item_id not in whole_keep_ids
                and int(item.quantity) > remaining_keep
            ]
            if not partial_candidates:
                return [], {}, self._get_destroy_split_block_reason(remaining_keep), 0

            partial_item = min(
                partial_candidates,
                key=lambda item: (
                    max(1, int(item.quantity)),
                    str(item.name or "").lower(),
                    int(item.item_id),
                ),
            )
            keep_quantities[int(partial_item.item_id)] = remaining_keep

        planned_actions: list[PlannedDestroyAction] = []
        for item in items:
            source_quantity = max(1, int(item.quantity))
            keep_quantity = max(0, int(keep_quantities.get(int(item.item_id), 0)))
            destroy_quantity = max(0, source_quantity - keep_quantity)
            if destroy_quantity <= 0:
                continue
            planned_actions.append(
                PlannedDestroyAction(
                    item_id=int(item.item_id),
                    model_id=int(item.model_id),
                    label=str(item.name or f"Model {int(item.model_id)}"),
                    quantity_to_destroy=destroy_quantity,
                    source_quantity=source_quantity,
                    keep_quantity=keep_quantity,
                    requires_split=keep_quantity > 0 and destroy_quantity < source_quantity,
                )
            )
        requires_external_free_slot = 0
        if any(bool(action.requires_split) for action in planned_actions) and not any(not bool(action.requires_split) for action in planned_actions):
            requires_external_free_slot = remaining_keep
        return planned_actions, keep_quantities, "", requires_external_free_slot

    def _plan_material_sales(
        self,
        matching_items: list[InventoryItemInfo],
        working_quantities: dict[int, int],
        keep_count: int,
    ) -> list[PlannedMaterialSale]:
        keep_count = max(0, int(keep_count))
        if not matching_items:
            return []

        rows: list[dict[str, object]] = []
        reserved_total = 0
        for item in matching_items:
            quantity = max(0, int(working_quantities.get(item.item_id, 0)))
            if quantity <= 0:
                continue
            batch_size = max(1, int(self._get_material_batch_size(item.model_id)))
            reserved = quantity % batch_size
            reserved_total += reserved
            rows.append(
                {
                    "item": item,
                    "quantity": quantity,
                    "reserved": reserved,
                    "batch_size": batch_size,
                    "merchant_type": self._get_material_merchant_type_by_model(item.model_id),
                }
            )

        extra_keep_needed = max(0, keep_count - reserved_total)
        rows.sort(key=lambda entry: int(entry["quantity"]))
        for row in rows:
            if extra_keep_needed <= 0:
                break
            quantity = int(row["quantity"])
            reserved = int(row["reserved"])
            batch_size = max(1, int(row["batch_size"]))
            while extra_keep_needed > 0 and (reserved + batch_size) <= quantity:
                reserved += batch_size
                extra_keep_needed -= batch_size
            row["reserved"] = reserved

        planned_sales: list[PlannedMaterialSale] = []
        for row in rows:
            item = row["item"]
            if not isinstance(item, InventoryItemInfo):
                continue
            quantity = int(row["quantity"])
            reserved = int(row["reserved"])
            batch_size = max(1, int(row["batch_size"]))
            merchant_type = str(row["merchant_type"])
            quantity_to_sell = max(0, quantity - reserved)
            batches_to_sell = quantity_to_sell // batch_size
            if batches_to_sell <= 0:
                continue
            sell_quantity = batches_to_sell * batch_size
            working_quantities[item.item_id] = max(0, quantity - sell_quantity)
            planned_sales.append(
                PlannedMaterialSale(
                    merchant_type=merchant_type,
                    item_id=item.item_id,
                    model_id=item.model_id,
                    label=item.name,
                    batches_to_sell=batches_to_sell,
                    quantity_to_sell=sell_quantity,
                    batch_size=batch_size,
                )
            )
        return planned_sales

    def _collect_enabled_sell_rules(self) -> list[tuple[int, SellRule]]:
        enabled_sell_rules: list[tuple[int, SellRule]] = []
        seen_rule_ids: set[str] = set()
        for rule_index, raw_sell_rule in enumerate(self.sell_rules):
            sell_rule = _normalize_sell_rule(raw_sell_rule)
            if sell_rule is None or not sell_rule.enabled:
                continue
            sell_rule.rule_id = _ensure_unique_rule_id(
                sell_rule.rule_id,
                seen_ids=seen_rule_ids,
                prefix="sell",
                fallback_seed=f"{rule_index}:{sell_rule.kind}:{sell_rule.name}",
            )
            enabled_sell_rules.append((rule_index, sell_rule))
        return enabled_sell_rules

    def _collect_enabled_destroy_rules(self) -> list[tuple[int, DestroyRule]]:
        enabled_destroy_rules: list[tuple[int, DestroyRule]] = []
        for rule_index, raw_destroy_rule in enumerate(self.destroy_rules):
            destroy_rule = _normalize_destroy_rule(raw_destroy_rule)
            if not destroy_rule.enabled:
                continue
            enabled_destroy_rules.append((rule_index, destroy_rule))
        return enabled_destroy_rules

    def _plan_destroy_rule(
        self,
        plan: PlanResult,
        items: list[InventoryItemInfo],
        rule: DestroyRule,
        rule_index: int,
        claimed_item_ids: set[int],
        enabled_sell_rules: list[tuple[int, SellRule]],
    ) -> None:
        include_protected_items = bool(self.destroy_include_protected_items)
        candidate_label = DESTROY_KIND_LABELS.get(rule.kind, "Destroy Rule")
        rule_reference = self._format_destroy_rule_reference(rule_index, rule)
        if rule.kind in (DESTROY_KIND_EXPLICIT_MODELS, DESTROY_KIND_MATERIALS):
            whitelist_targets = _normalize_whitelist_targets(getattr(rule, "whitelist_targets", []))
            if not whitelist_targets:
                missing_reason = "No material model whitelist configured." if rule.kind == DESTROY_KIND_MATERIALS else "No explicit model whitelist configured."
                plan.entries.append(
                    ExecutionPlanEntry(
                        "destroy",
                        MERCHANT_TYPE_INVENTORY,
                        candidate_label,
                        0,
                        PLAN_STATE_SKIPPED,
                        missing_reason,
                    )
                )
                return

            target_plans: list[dict[str, object]] = []
            for target in whitelist_targets:
                target_model_id = max(0, int(target.model_id))
                target_keep_count = max(0, int(target.keep_count))
                target_label = self._format_model_label(target_model_id)
                matching_items = [
                    item
                    for item in items
                    if item.item_id not in claimed_item_ids
                    and (
                        (rule.kind == DESTROY_KIND_EXPLICIT_MODELS and item.model_id == target_model_id)
                        or (rule.kind == DESTROY_KIND_MATERIALS and item.is_material and item.model_id == target_model_id)
                    )
                ]
                if not matching_items:
                    missing_reason = "No matching material items found." if rule.kind == DESTROY_KIND_MATERIALS else "No matching inventory items found."
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "destroy",
                            MERCHANT_TYPE_INVENTORY,
                            target_label,
                            0,
                            PLAN_STATE_SKIPPED,
                            missing_reason,
                        )
                    )
                    continue

                protected_items: list[tuple[InventoryItemInfo, str]] = []
                destroy_pool: list[tuple[InventoryItemInfo, str]] = []
                for item in matching_items:
                    hard_protection = self._get_hard_protection_hit(item, enabled_sell_rules)
                    protection_reason = hard_protection[1] if hard_protection is not None else ""
                    if protection_reason and not include_protected_items:
                        protected_items.append((item, protection_reason))
                    else:
                        destroy_pool.append((item, protection_reason))

                keep_quantities: dict[int, int] = {}
                planned_actions: list[PlannedDestroyAction] = []
                destroy_block_reason = ""
                split_keep_quantity_needed = 0
                effective_keep_count = max(0, target_keep_count)
                if not include_protected_items:
                    effective_keep_count = max(
                        0,
                        effective_keep_count - sum(max(1, int(item.quantity)) for item, _reason in protected_items),
                    )

                destroy_items = [item for item, _reason in destroy_pool]
                if any(int(item.quantity) > 1 for item in destroy_items):
                    planned_actions, keep_quantities, destroy_block_reason, split_keep_quantity_needed = self._plan_stackable_destroy_actions(
                        destroy_items,
                        effective_keep_count,
                    )
                else:
                    keep_ids = self._choose_keep_subset(destroy_items, effective_keep_count)
                    keep_quantities = {
                        int(item.item_id): max(1, int(item.quantity))
                        for item in destroy_items
                        if item.item_id in keep_ids
                    }
                    planned_actions = [
                        PlannedDestroyAction(
                            item_id=int(item.item_id),
                            model_id=int(item.model_id),
                            label=str(item.name or f"Model {int(item.model_id)}"),
                            quantity_to_destroy=max(1, int(item.quantity)),
                            source_quantity=max(1, int(item.quantity)),
                        )
                        for item in destroy_items
                        if item.item_id not in keep_ids
                    ]

                target_plans.append(
                    {
                        "label": target_label,
                        "target_keep_count": target_keep_count,
                        "matching_items": matching_items,
                        "protected_items": protected_items,
                        "destroy_pool": destroy_pool,
                        "keep_quantities": keep_quantities,
                        "planned_actions": planned_actions,
                        "destroy_block_reason": destroy_block_reason,
                        "split_keep_quantity_needed": split_keep_quantity_needed,
                    }
                )

            has_empty_slot_now = self._find_inventory_empty_slot(items) is not None
            has_non_split_destroy_anywhere = any(not bool(action.requires_split) for action in plan.destroy_actions)
            has_non_split_destroy_anywhere = has_non_split_destroy_anywhere or any(
                any(not bool(action.requires_split) for action in target_plan["planned_actions"])
                for target_plan in target_plans
                if not str(target_plan["destroy_block_reason"] or "").strip()
            )

            total_matched = 0
            total_protected = 0
            total_kept_quantity = 0
            total_planned_destroys = 0
            total_planned_destroy_quantity = 0
            for target_plan in target_plans:
                matching_items = list(target_plan["matching_items"])
                protected_items = list(target_plan["protected_items"])
                destroy_pool = list(target_plan["destroy_pool"])
                keep_quantities = dict(target_plan["keep_quantities"])
                planned_actions = list(target_plan["planned_actions"])
                destroy_block_reason = str(target_plan["destroy_block_reason"] or "")
                split_keep_quantity_needed = max(0, int(target_plan["split_keep_quantity_needed"]))
                target_keep_count = max(0, int(target_plan["target_keep_count"]))
                target_label = str(target_plan["label"] or candidate_label)

                for item in matching_items:
                    claimed_item_ids.add(item.item_id)

                if not destroy_block_reason and split_keep_quantity_needed > 0 and not (has_empty_slot_now or has_non_split_destroy_anywhere):
                    destroy_block_reason = self._get_destroy_split_block_reason(split_keep_quantity_needed)
                    keep_quantities = {}
                    planned_actions = []

                planned_actions_by_item_id = {
                    int(action.item_id): action
                    for action in planned_actions
                }
                kept_quantity_total = sum(max(0, int(quantity)) for quantity in keep_quantities.values())
                planned_destroys = 0
                planned_destroy_quantity = 0

                total_matched += len(matching_items)
                total_protected += len(protected_items)
                total_kept_quantity += kept_quantity_total

                for item, protection_reason in protected_items:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "destroy",
                            MERCHANT_TYPE_INVENTORY,
                            item.name,
                            item.quantity,
                            PLAN_STATE_SKIPPED,
                            f"Blocked by {rule_reference}: {protection_reason}",
                            model_id=item.model_id,
                        )
                    )

                if destroy_block_reason:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "destroy",
                            MERCHANT_TYPE_INVENTORY,
                            target_label,
                            0,
                            PLAN_STATE_SKIPPED,
                            f"Blocked by {rule_reference}: {destroy_block_reason}",
                        )
                    )

                for item, protection_reason in destroy_pool:
                    keep_quantity = max(0, int(keep_quantities.get(int(item.item_id), 0)))
                    action = planned_actions_by_item_id.get(int(item.item_id))
                    if action is not None:
                        reason_parts = [f"Matched by {rule_reference}."]
                        if action.requires_split:
                            reason_parts.append(f"Split stack to keep {max(0, int(action.keep_quantity))} unit(s).")
                        if protection_reason:
                            reason_parts.append(f"Included protected item: {protection_reason}")
                        plan.destroy_actions.append(action)
                        plan.destroy_item_ids.append(int(action.item_id))
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "destroy",
                                MERCHANT_TYPE_INVENTORY,
                                item.name,
                                max(0, int(action.quantity_to_destroy)),
                                PLAN_STATE_WILL_EXECUTE,
                                " ".join(reason_parts),
                                model_id=item.model_id,
                            )
                        )
                        planned_destroys += 1
                        planned_destroy_quantity += max(0, int(action.quantity_to_destroy))

                    if keep_quantity > 0:
                        keep_reason = (
                            f"Kept by {rule_reference}: reserved to satisfy keep count {target_keep_count}."
                            if keep_quantity >= max(1, int(item.quantity))
                            else (
                                f"Kept by {rule_reference}: reserved {keep_quantity} unit(s) "
                                f"to satisfy keep count {target_keep_count}."
                            )
                        )
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "destroy",
                                MERCHANT_TYPE_INVENTORY,
                                item.name,
                                keep_quantity,
                                PLAN_STATE_SKIPPED,
                                keep_reason,
                                model_id=item.model_id,
                            )
                        )

                if planned_destroys <= 0 and not protected_items and kept_quantity_total > 0 and not destroy_block_reason:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "destroy",
                            MERCHANT_TYPE_INVENTORY,
                            target_label,
                            0,
                            PLAN_STATE_SKIPPED,
                            f"Kept by {rule_reference}: matching items were reserved to satisfy keep count {target_keep_count}.",
                        )
                    )

                total_planned_destroys += planned_destroys
                total_planned_destroy_quantity += planned_destroy_quantity

            self._debug_log(
                f"{candidate_label}: matched={total_matched} protected={total_protected} "
                f"kept_quantity={total_kept_quantity} planned_destroys={total_planned_destroys} "
                f"planned_destroy_quantity={total_planned_destroy_quantity} include_protected={include_protected_items}"
            )
            return

        matching_items: list[InventoryItemInfo] = []
        had_category_candidate = False
        had_rarity_candidate = False
        for item in items:
            if item.item_id in claimed_item_ids:
                continue
            if rule.kind == DESTROY_KIND_WEAPONS:
                if not item.is_weapon_like:
                    continue
            elif rule.kind == DESTROY_KIND_ARMOR:
                if not item.is_armor_piece:
                    continue
            else:
                continue

            had_category_candidate = True
            if not self._rule_matches_selected_rarity(item, rule):
                continue
            had_rarity_candidate = True
            matching_items.append(item)

        if not matching_items:
            reason = (
                "No matching items found for the enabled rarities."
                if had_category_candidate and not had_rarity_candidate
                else "No matching inventory items found."
            )
            plan.entries.append(
                ExecutionPlanEntry(
                    "destroy",
                    MERCHANT_TYPE_INVENTORY,
                    candidate_label,
                    0,
                    PLAN_STATE_SKIPPED,
                    reason,
                )
            )
            return

        for item in matching_items:
            claimed_item_ids.add(item.item_id)

        protected_items: list[tuple[InventoryItemInfo, str]] = []
        destroy_pool: list[tuple[InventoryItemInfo, str]] = []
        for item in matching_items:
            hard_protection = self._get_hard_protection_hit(item, enabled_sell_rules)
            protection_reason = hard_protection[1] if hard_protection is not None else ""
            if protection_reason and not include_protected_items:
                protected_items.append((item, protection_reason))
            else:
                destroy_pool.append((item, protection_reason))

        planned_actions = [
            PlannedDestroyAction(
                item_id=int(item.item_id),
                model_id=int(item.model_id),
                label=str(item.name or f"Model {int(item.model_id)}"),
                quantity_to_destroy=max(1, int(item.quantity)),
                source_quantity=max(1, int(item.quantity)),
            )
            for item, _reason in destroy_pool
        ]
        planned_actions_by_item_id = {
            int(action.item_id): action
            for action in planned_actions
        }

        planned_destroys = 0
        planned_destroy_quantity = 0
        for item, protection_reason in protected_items:
            plan.entries.append(
                ExecutionPlanEntry(
                    "destroy",
                    MERCHANT_TYPE_INVENTORY,
                    item.name,
                    item.quantity,
                    PLAN_STATE_SKIPPED,
                    f"Blocked by {rule_reference}: {protection_reason}",
                    model_id=item.model_id,
                )
            )

        for item, protection_reason in destroy_pool:
            action = planned_actions_by_item_id.get(int(item.item_id))
            if action is None:
                continue
            reason_parts = [f"Matched by {rule_reference}."]
            if protection_reason:
                reason_parts.append(f"Included protected item: {protection_reason}")
            plan.destroy_actions.append(action)
            plan.destroy_item_ids.append(int(action.item_id))
            plan.entries.append(
                ExecutionPlanEntry(
                    "destroy",
                    MERCHANT_TYPE_INVENTORY,
                    item.name,
                    max(0, int(action.quantity_to_destroy)),
                    PLAN_STATE_WILL_EXECUTE,
                    " ".join(reason_parts),
                    model_id=item.model_id,
                )
            )
            planned_destroys += 1
            planned_destroy_quantity += max(0, int(action.quantity_to_destroy))

        self._debug_log(
            f"{candidate_label}: matched={len(matching_items)} protected={len(protected_items)} "
            f"kept_quantity=0 planned_destroys={planned_destroys} "
            f"planned_destroy_quantity={planned_destroy_quantity} include_protected={include_protected_items}"
        )

    def _plan_destroy_actions(
        self,
        plan: PlanResult,
        items: list[InventoryItemInfo],
        enabled_destroy_rules: list[tuple[int, DestroyRule]],
        enabled_sell_rules: list[tuple[int, SellRule]],
        claimed_item_ids: set[int],
    ) -> None:
        for rule_index, destroy_rule in enabled_destroy_rules:
            self._plan_destroy_rule(
                plan,
                items,
                destroy_rule,
                rule_index,
                claimed_item_ids,
                enabled_sell_rules,
            )

    def _build_simulated_model_counts(self, items: list[InventoryItemInfo], plan: PlanResult) -> dict[int, int]:
        simulated_counts = self._get_inventory_model_counts(items)
        item_by_id = {
            int(item.item_id): item
            for item in items
            if int(item.item_id) > 0
        }

        def subtract_model_quantity(model_id: int, quantity: int):
            current_quantity = max(0, int(simulated_counts.get(model_id, 0)))
            next_quantity = max(0, current_quantity - max(0, int(quantity)))
            if next_quantity > 0:
                simulated_counts[model_id] = next_quantity
            else:
                simulated_counts.pop(model_id, None)

        material_sale_quantities_by_item_id: dict[int, int] = {}

        if plan.destroy_actions:
            for destroy_action in plan.destroy_actions:
                subtract_model_quantity(destroy_action.model_id, destroy_action.quantity_to_destroy)
        else:
            for item_id in plan.destroy_item_ids:
                item = item_by_id.get(int(item_id))
                if item is not None:
                    subtract_model_quantity(item.model_id, item.quantity)

        for material_sale in plan.material_sales:
            safe_item_id = int(material_sale.item_id)
            material_sale_quantities_by_item_id[safe_item_id] = (
                max(0, int(material_sale_quantities_by_item_id.get(safe_item_id, 0)))
                + max(0, int(material_sale.quantity_to_sell))
            )
            subtract_model_quantity(material_sale.model_id, material_sale.quantity_to_sell)

        for item_id in plan.merchant_sell_item_ids:
            item = item_by_id.get(int(item_id))
            if item is not None:
                material_sold_quantity = max(0, int(material_sale_quantities_by_item_id.get(int(item_id), 0)))
                merchant_quantity = max(0, int(item.quantity) - material_sold_quantity)
                if merchant_quantity > 0:
                    subtract_model_quantity(item.model_id, merchant_quantity)

        for trader_sale in plan.rune_trader_sales:
            item = item_by_id.get(int(trader_sale.item_id))
            if item is not None:
                subtract_model_quantity(item.model_id, item.quantity)

        return simulated_counts

    def _plan_buy_actions(
        self,
        plan: PlanResult,
        sim_model_counts: dict[int, int],
        *,
        sim_inventory_items: list[InventoryItemInfo] | None = None,
        storage_items: list[InventoryItemInfo] | None = None,
    ) -> None:
        supported_map = bool(plan.supported_map)
        supported_reason = str(plan.supported_reason or "")
        coords = dict(plan.coords)
        sim_inventory_items = list(sim_inventory_items or [])
        storage_items = list(storage_items or [])
        sim_storage_items = [replace(item, quantity=max(0, int(item.quantity))) for item in storage_items]
        inventory_identifier_counts = self._get_standalone_rune_identifier_counts(sim_inventory_items)
        storage_model_counts = self._get_inventory_model_counts(sim_storage_items) if plan.storage_exact else {}
        storage_identifier_counts = self._get_standalone_rune_identifier_counts(sim_storage_items) if plan.storage_exact else {}

        for buy_rule in self.buy_rules:
            normalized_buy_rule = _normalize_buy_rule(buy_rule)
            if normalized_buy_rule is None:
                continue
            buy_rule = normalized_buy_rule
            if not buy_rule.enabled:
                continue

            if buy_rule.kind == BUY_KIND_MATERIAL_TARGET:
                if not buy_rule.material_targets:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "buy",
                            MERCHANT_TYPE_MATERIALS,
                            BUY_KIND_LABELS[buy_rule.kind],
                            0,
                            PLAN_STATE_SKIPPED,
                            "No crafting materials selected.",
                        )
                    )
                    continue

                for material_target in buy_rule.material_targets:
                    material_model_id = max(0, int(material_target.model_id))
                    material_label = self._format_model_label(material_model_id)
                    if material_model_id <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_MATERIALS,
                                BUY_KIND_LABELS[buy_rule.kind],
                                0,
                                PLAN_STATE_SKIPPED,
                                "Crafting material model is required.",
                            )
                        )
                        continue

                    material_entry = self._get_material_catalog_entry(material_model_id)
                    if material_entry is None:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_MATERIALS,
                                material_label,
                                0,
                                PLAN_STATE_SKIPPED,
                                "Selected item is not a supported crafting material.",
                            )
                        )
                        continue

                    merchant_type = self._get_material_merchant_type_by_model(material_model_id)
                    merchant_coords = coords.get(merchant_type)
                    if not supported_map:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                action_type="buy",
                                merchant_type=merchant_type,
                                label=material_label,
                                quantity=0,
                                state=PLAN_STATE_SKIPPED,
                                reason=supported_reason,
                            )
                        )
                        continue

                    if merchant_coords is None:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                action_type="buy",
                                merchant_type=merchant_type,
                                label=material_label,
                                quantity=0,
                                state=PLAN_STATE_SKIPPED,
                                reason=f"{MERCHANT_TYPE_LABELS[merchant_type]} selector was not resolved in the current map.",
                            )
                        )
                        continue

                    current_count = sim_model_counts.get(material_model_id, 0)
                    missing = max(0, int(material_target.target_count) - current_count)
                    if missing <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry("buy", merchant_type, material_label, 0, PLAN_STATE_SKIPPED, "Target already met.")
                        )
                        continue

                    batch_size = self._get_material_batch_size(material_model_id)
                    if batch_size > 1:
                        needed = ((missing + batch_size - 1) // batch_size) * batch_size
                        if material_target.max_per_run > 0:
                            capped_needed = (int(material_target.max_per_run) // batch_size) * batch_size
                            if capped_needed <= 0:
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "buy",
                                        merchant_type,
                                        material_label,
                                        0,
                                        PLAN_STATE_SKIPPED,
                                        f"Common materials buy in lots of {batch_size}; Max Per Run is below one full batch.",
                                    )
                                )
                                continue
                            needed = min(needed, capped_needed)
                    else:
                        needed = self._apply_max_per_run(missing, material_target.max_per_run)

                    if needed <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry("buy", merchant_type, material_label, 0, PLAN_STATE_SKIPPED, "Target already met.")
                        )
                        continue

                    sim_model_counts[material_model_id] = current_count + needed
                    plan.material_buys.append(
                        PlannedMaterialBuy(
                            merchant_type=merchant_type,
                            model_id=material_model_id,
                            quantity=needed,
                            label=material_label,
                            batch_size=batch_size,
                        )
                    )
                    reason = "Character gold only."
                    if batch_size > 1:
                        reason = f"{needed // batch_size} full trader batch(es) of {batch_size}. Character gold only."
                    plan.entries.append(
                        ExecutionPlanEntry("buy", merchant_type, material_label, needed, PLAN_STATE_WILL_EXECUTE, reason)
                    )
                continue

            if buy_rule.kind == BUY_KIND_MERCHANT_STOCK:
                merchant_stock_targets = _normalize_merchant_stock_targets(buy_rule.merchant_stock_targets)
                if not merchant_stock_targets:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "buy",
                            MERCHANT_TYPE_MERCHANT,
                            BUY_KIND_LABELS[buy_rule.kind],
                            0,
                            PLAN_STATE_SKIPPED,
                            "No merchant stock items selected.",
                        )
                    )
                    continue
                merchant_type = _get_buy_rule_merchant_type(buy_rule)
                merchant_coords = coords.get(merchant_type)
                for merchant_stock_target in merchant_stock_targets:
                    merchant_stock_model_id = max(0, int(merchant_stock_target.model_id))
                    model_label = self._format_model_label(merchant_stock_model_id)
                    if merchant_stock_model_id <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                merchant_type,
                                BUY_KIND_LABELS[buy_rule.kind],
                                0,
                                PLAN_STATE_SKIPPED,
                                "Model ID is required.",
                            )
                        )
                        continue
                    if not supported_map:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                action_type="buy",
                                merchant_type=merchant_type,
                                label=model_label,
                                quantity=0,
                                state=PLAN_STATE_SKIPPED,
                                reason=supported_reason,
                            )
                        )
                        continue

                    if merchant_coords is None:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                action_type="buy",
                                merchant_type=merchant_type,
                                label=model_label,
                                quantity=0,
                                state=PLAN_STATE_SKIPPED,
                                reason=f"{MERCHANT_TYPE_LABELS[merchant_type]} selector was not resolved in the current map.",
                            )
                        )
                        continue

                    current_count = sim_model_counts.get(merchant_stock_model_id, 0)
                    needed = self._apply_max_per_run(
                        int(merchant_stock_target.target_count) - current_count,
                        int(merchant_stock_target.max_per_run),
                    )
                    if needed <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                merchant_type,
                                model_label,
                                0,
                                PLAN_STATE_SKIPPED,
                                "Target already met.",
                            )
                        )
                        continue
                    sim_model_counts[merchant_stock_model_id] = current_count + needed
                    plan.merchant_stock_buys.append(
                        PlannedMerchantBuy(
                            model_id=merchant_stock_model_id,
                            quantity=needed,
                            label=model_label,
                        )
                    )
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "buy",
                            merchant_type,
                            model_label,
                            needed,
                            PLAN_STATE_CONDITIONAL,
                            "Will attempt this buy only if the currently opened merchant offers the item.",
                        )
                    )
                continue

            if buy_rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
                rune_targets = _normalize_rune_trader_targets(buy_rule.rune_targets)
                if not rune_targets:
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "buy",
                            MERCHANT_TYPE_RUNE_TRADER,
                            BUY_KIND_LABELS[buy_rule.kind],
                            0,
                            PLAN_STATE_SKIPPED,
                            "No rune or insignia targets selected.",
                        )
                    )
                    continue

                rune_trader_coords = coords.get(MERCHANT_TYPE_RUNE_TRADER)
                for rune_target in rune_targets:
                    identifier = _normalize_rune_identifier(rune_target.identifier)
                    label = self._get_rune_label(identifier)
                    if not identifier:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_RUNE_TRADER,
                                BUY_KIND_LABELS[buy_rule.kind],
                                0,
                                PLAN_STATE_SKIPPED,
                                "Rune or insignia identifier is required.",
                            )
                        )
                        continue

                    if not supported_map:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                action_type="buy",
                                merchant_type=MERCHANT_TYPE_RUNE_TRADER,
                                label=label,
                                quantity=0,
                                state=PLAN_STATE_SKIPPED,
                                reason=supported_reason,
                            )
                        )
                        continue

                    stock_key = _make_identifier_stock_key(identifier)
                    stock_counts = self._build_stock_location_counts(
                        stock_key,
                        label,
                        inventory_model_counts=sim_model_counts,
                        inventory_identifier_counts=inventory_identifier_counts,
                        storage_model_counts=storage_model_counts,
                        storage_identifier_counts=storage_identifier_counts,
                        storage_exact=plan.storage_exact,
                    )
                    missing = max(0, int(rune_target.target_count) - int(stock_counts.inventory_count))
                    needed = self._apply_max_per_run(missing, int(rune_target.max_per_run))
                    if needed <= 0:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_RUNE_TRADER,
                                label,
                                0,
                                PLAN_STATE_SKIPPED,
                                "Target already met.",
                            )
                        )
                        continue

                    if not plan.storage_exact:
                        reason_parts = [
                            f"Inventory is short by up to {needed}.",
                            "Open Xunlai for exact storage scan so Merchant Rules can plan withdraws before any Rune Trader buy.",
                        ]
                        if rune_trader_coords is None:
                            reason_parts.append("Rune Trader selector is also unresolved in the current map.")
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_RUNE_TRADER,
                                label,
                                needed,
                                PLAN_STATE_CONDITIONAL,
                                " ".join(reason_parts),
                            )
                        )
                        continue

                    withdraw_quantity = min(
                        needed,
                        max(0, int(stock_counts.storage_count)),
                    )
                    if withdraw_quantity > 0:
                        transfers = self._get_storage_transfer_items_for_stock_key(
                            sim_storage_items,
                            stock_key,
                            quantity=withdraw_quantity,
                            label=label,
                            direction=STORAGE_TRANSFER_WITHDRAW,
                        )
                        planned_withdraw_quantity = sum(max(0, int(transfer.quantity)) for transfer in transfers)
                        if planned_withdraw_quantity > 0:
                            plan.storage_transfers.extend(transfers)
                            plan.entries.append(
                                ExecutionPlanEntry(
                                    "withdraw",
                                    MERCHANT_TYPE_STORAGE,
                                    label,
                                    planned_withdraw_quantity,
                                    PLAN_STATE_WILL_EXECUTE,
                                    "Withdraw from Xunlai before buying.",
                                )
                            )
                            self._adjust_stock_count_for_key(
                                stock_key,
                                -planned_withdraw_quantity,
                                model_counts=storage_model_counts,
                                identifier_counts=storage_identifier_counts,
                            )
                            self._adjust_stock_count_for_key(
                                stock_key,
                                planned_withdraw_quantity,
                                model_counts=sim_model_counts,
                                identifier_counts=inventory_identifier_counts,
                            )
                            sim_storage_items = self._apply_planned_transfer_quantities(sim_storage_items, transfers)
                            needed -= planned_withdraw_quantity

                    if needed <= 0:
                        continue

                    if rune_trader_coords is None:
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "buy",
                                MERCHANT_TYPE_RUNE_TRADER,
                                label,
                                needed,
                                PLAN_STATE_SKIPPED,
                                "Rune Trader selector was not resolved in the current map after storage withdrawals.",
                            )
                        )
                        continue

                    plan.rune_trader_buys.append(
                        PlannedTraderBuy(
                            identifier=identifier,
                            quantity=needed,
                            label=label,
                        )
                    )
                    self._adjust_stock_count_for_key(
                        stock_key,
                        needed,
                        model_counts=sim_model_counts,
                        identifier_counts=inventory_identifier_counts,
                    )
                    plan.entries.append(
                        ExecutionPlanEntry(
                            "buy",
                            MERCHANT_TYPE_RUNE_TRADER,
                            label,
                            needed,
                            PLAN_STATE_CONDITIONAL,
                            "Will attempt this exact Rune Trader buy after any storage withdrawals if the trader currently offers the item.",
                        )
                    )

    def _build_plan(
        self,
        *,
        cleanup_only: bool = False,
        projected_preview: bool = False,
        ignore_travel_target: bool = False,
    ) -> PlanResult:
        started_at = time.perf_counter()
        projected_target_outpost_id = 0
        projected_target_outpost_name = ""
        projected_destination_context = False
        if not cleanup_only:
            target_outpost_id = 0 if ignore_travel_target else (max(0, int(self.target_outpost_id)) if self.auto_travel_enabled else 0)
            current_map_id = int(Map.GetMapID() or 0)
            if projected_preview:
                projected_target_outpost_id, projected_target_outpost_name = self._get_preview_projection_target()
                projected_destination_context = projected_target_outpost_id > 0 and bool(projected_target_outpost_name)
            if (
                not projected_destination_context
                and target_outpost_id > 0
                and not self._is_travel_target_reached(target_outpost_id, current_map_id)
            ):
                travel_plan = self._build_travel_preview(target_outpost_id)
                self._log_plan_summary("Plan built", travel_plan)
                self.last_plan_build_duration_ms = max(0.0, (time.perf_counter() - started_at) * 1000.0)
                return travel_plan

        if projected_destination_context:
            supported_map, supported_reason, coords = self._get_projected_supported_context(projected_target_outpost_id)
        else:
            supported_map, supported_reason, coords = self._get_supported_context()
        plan = PlanResult(
            supported_map=supported_map,
            supported_reason=supported_reason,
            coords=coords,
        )
        if not self._has_enabled_rules():
            self._debug_log("Plan build skipped inventory snapshot because no buy, sell, destroy, or cleanup rules are enabled.")
            self._log_plan_summary("Plan built", plan)
            self.last_plan_build_duration_ms = max(0.0, (time.perf_counter() - started_at) * 1000.0)
            return plan

        items = self._collect_inventory_items()
        model_counts = self._get_inventory_model_counts(items)
        plan.inventory_snapshot_captured = True
        plan.inventory_model_counts = dict(model_counts)
        plan.inventory_item_count = len(items)
        storage_context_ready = projected_destination_context or self._can_use_local_storage_actions()
        storage_api = getattr(GLOBAL_CACHE, "Inventory", None)
        storage_open = bool(storage_api is not None and bool(getattr(storage_api, "IsStorageOpen", lambda: False)()))
        storage_items: list[InventoryItemInfo] = []
        if self._has_enabled_rune_buy_rules():
            if storage_open:
                storage_items = self._collect_storage_items()
                plan.storage_plan_state = STORAGE_PLAN_STATE_EXACT_READY
                plan.storage_exact = True
            else:
                plan.storage_plan_state = STORAGE_PLAN_STATE_NEEDS_EXACT_SCAN
                plan.storage_exact = False

        enabled_sell_rules = self._collect_enabled_sell_rules()
        enabled_destroy_rules = self._collect_enabled_destroy_rules()
        claimed_item_ids: set[int] = set()
        self._plan_destroy_actions(plan, items, enabled_destroy_rules, enabled_sell_rules, claimed_item_ids)
        material_quantities = {
            item.item_id: item.quantity
            for item in items
            if item.is_material
        }

        if supported_map or storage_context_ready:
            for item in items:
                if item.item_id in claimed_item_ids:
                    continue
                hard_protection = self._get_hard_protection_match(item, enabled_sell_rules)
                if hard_protection is None:
                    continue
                rule_index, rule, destination, detail = hard_protection
                rule_reference = self._format_sell_rule_reference(rule_index, rule)
                claimed_item_ids.add(item.item_id)
                plan.entries.append(
                    ExecutionPlanEntry(
                        "sell",
                        destination,
                        item.name,
                        item.quantity,
                        PLAN_STATE_SKIPPED,
                        f"Hard-protected by {rule_reference}: {detail}",
                        model_id=item.model_id,
                    )
                )

        for rule_index, sell_rule in enabled_sell_rules:
            merchant_coords = coords.get(sell_rule.merchant_type)
            if not supported_map and not storage_context_ready:
                plan.entries.append(
                    ExecutionPlanEntry(
                        action_type="sell",
                        merchant_type=sell_rule.merchant_type,
                        label=SELL_KIND_LABELS[sell_rule.kind],
                        quantity=0,
                        state="skipped",
                        reason=supported_reason,
                    )
                )
                continue

            rule_reference = self._format_sell_rule_reference(rule_index, sell_rule)
            if sell_rule.kind in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                self._plan_equippable_rule_sales(
                    plan=plan,
                    items=items,
                    rule=sell_rule,
                    rule_index=rule_index,
                    claimed_item_ids=claimed_item_ids,
                    coords=coords,
                )
                continue

            if sell_rule.kind == SELL_KIND_COMMON_MATERIALS:
                material_targets = _normalize_whitelist_targets(getattr(sell_rule, "whitelist_targets", []))
                if not material_targets:
                    plan.entries.append(
                        ExecutionPlanEntry("sell", sell_rule.merchant_type, SELL_KIND_LABELS[sell_rule.kind], 0, "skipped", "No material model whitelist configured.")
                    )
                    continue

                for material_target in material_targets:
                    material_model_id = max(0, int(material_target.model_id))
                    target_keep_count = max(0, int(material_target.keep_count))
                    target_label = self._format_model_label(material_model_id)
                    matching_items = [
                        item
                        for item in items
                        if item.item_id not in claimed_item_ids
                        and item.is_material
                        and item.model_id == material_model_id
                        and int(material_quantities.get(item.item_id, 0)) > 0
                    ]
                    if not matching_items:
                        plan.entries.append(
                            ExecutionPlanEntry("sell", sell_rule.merchant_type, target_label, 0, "skipped", "No matching material items found.")
                        )
                        continue

                    working_quantities = {
                        item.item_id: max(0, int(material_quantities.get(item.item_id, item.quantity)))
                        for item in matching_items
                    }
                    material_sales = self._plan_material_sales(matching_items, working_quantities, target_keep_count)
                    for item in matching_items:
                        claimed_item_ids.add(item.item_id)

                    sold_quantities_by_item_id = {
                        sale.item_id: max(0, int(sale.quantity_to_sell))
                        for sale in material_sales
                    }
                    for sale in material_sales:
                        sale_reason = (
                            f"{sale.batches_to_sell} full trader batch(es) of {sale.batch_size}."
                            if int(sale.batch_size) > 1
                            else f"{sale.quantity_to_sell} individual trade(s)."
                        )
                        if coords.get(sale.merchant_type) is None:
                            plan.entries.append(
                                ExecutionPlanEntry(
                                    "sell",
                                    sale.merchant_type,
                                    sale.label,
                                    sale.quantity_to_sell,
                                    PLAN_STATE_SKIPPED,
                                    (
                                        f"Blocked by {rule_reference}: "
                                        f"{MERCHANT_TYPE_LABELS[sale.merchant_type]} selector was not resolved in the current map."
                                    ),
                                    model_id=sale.model_id,
                                )
                            )
                        else:
                            plan.material_sales.append(sale)
                            plan.entries.append(
                                ExecutionPlanEntry(
                                    "sell",
                                    sale.merchant_type,
                                    sale.label,
                                    sale.quantity_to_sell,
                                    PLAN_STATE_WILL_EXECUTE,
                                    sale_reason,
                                    model_id=sale.model_id,
                                )
                            )
                    fallback_merchant_coords = coords.get(MERCHANT_TYPE_MERCHANT)
                    for item in matching_items:
                        remaining_quantity = max(0, int(working_quantities.get(item.item_id, 0)))
                        if remaining_quantity <= 0:
                            continue
                        sold_quantity = sold_quantities_by_item_id.get(item.item_id, 0)
                        item_merchant_type = self._get_material_merchant_type_by_model(item.model_id)
                        batch_size = max(1, int(self._get_material_batch_size(item.model_id)))
                        if (
                            target_keep_count <= 0
                            and item_merchant_type == MERCHANT_TYPE_MATERIALS
                            and remaining_quantity < batch_size
                        ):
                            merchant_reason = (
                                "Merchant fallback after selling full trader batches; leftover common-material quantity is below the trader batch size."
                                if sold_quantity > 0
                                else "Merchant fallback because the common-material quantity is below the trader batch size."
                            )
                            if fallback_merchant_coords is None:
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "sell",
                                        MERCHANT_TYPE_MERCHANT,
                                        item.name,
                                        remaining_quantity,
                                        PLAN_STATE_SKIPPED,
                                        (
                                            f"Blocked by {rule_reference}: "
                                            f"{MERCHANT_TYPE_LABELS[MERCHANT_TYPE_MERCHANT]} selector was not resolved in the current map."
                                        ),
                                        model_id=item.model_id,
                                    )
                                )
                            else:
                                plan.merchant_sell_item_ids.append(item.item_id)
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "sell",
                                        MERCHANT_TYPE_MERCHANT,
                                        item.name,
                                        remaining_quantity,
                                        PLAN_STATE_WILL_EXECUTE,
                                        merchant_reason,
                                        model_id=item.model_id,
                                    )
                                )
                            continue
                        keep_reason = (
                            (
                                f"Kept by {rule_reference}: {remaining_quantity} unit(s) remain after selling full trader batches."
                                if batch_size > 1
                                else f"Kept by {rule_reference}: {remaining_quantity} unit(s) remain after selling individual trades."
                            )
                            if sold_quantity > 0
                            else (
                                f"Kept by {rule_reference}: no tradable full trader batches remained after keep count."
                                if batch_size > 1
                                else f"Kept by {rule_reference}: reserved to satisfy keep count {target_keep_count}."
                            )
                        )
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "sell",
                                item_merchant_type,
                                item.name,
                                remaining_quantity,
                                PLAN_STATE_SKIPPED,
                                keep_reason,
                                model_id=item.model_id,
                            )
                        )
                continue

            if sell_rule.kind == SELL_KIND_EXPLICIT_MODELS:
                explicit_targets = _normalize_whitelist_targets(getattr(sell_rule, "whitelist_targets", []))
                if not explicit_targets:
                    plan.entries.append(
                        ExecutionPlanEntry("sell", sell_rule.merchant_type, SELL_KIND_LABELS[sell_rule.kind], 0, "skipped", "No explicit model whitelist configured.")
                    )
                    continue

                for explicit_target in explicit_targets:
                    target_model_id = max(0, int(explicit_target.model_id))
                    target_keep_count = max(0, int(explicit_target.keep_count))
                    target_label = self._format_model_label(target_model_id)
                    matching_items = [
                        item
                        for item in items
                        if item.item_id not in claimed_item_ids and item.model_id == target_model_id
                    ]
                    if not matching_items:
                        plan.entries.append(
                            ExecutionPlanEntry("sell", sell_rule.merchant_type, target_label, 0, "skipped", "No matching inventory items found.")
                        )
                        continue

                    keep_ids = self._choose_keep_subset(matching_items, target_keep_count)
                    for item in matching_items:
                        claimed_item_ids.add(item.item_id)
                        if item.item_id not in keep_ids:
                            continue
                        item_destination = self._get_explicit_sell_destination(item)
                        plan.entries.append(
                            ExecutionPlanEntry(
                                "sell",
                                item_destination,
                                item.name,
                                item.quantity,
                                PLAN_STATE_SKIPPED,
                                f"Kept by {rule_reference}: reserved to satisfy keep count {target_keep_count}.",
                                model_id=item.model_id,
                            )
                        )

                    sell_items = [item for item in matching_items if item.item_id not in keep_ids]
                    if not sell_items:
                        continue

                    sell_items_by_destination: dict[str, list[InventoryItemInfo]] = {}
                    for item in sell_items:
                        item_destination = self._get_explicit_sell_destination(item)
                        sell_items_by_destination.setdefault(item_destination, []).append(item)

                    for destination, destination_items in sell_items_by_destination.items():
                        if destination == MERCHANT_TYPE_MERCHANT:
                            merchant_coords = coords.get(MERCHANT_TYPE_MERCHANT)
                            if merchant_coords is None:
                                for item in destination_items:
                                    plan.entries.append(
                                        ExecutionPlanEntry(
                                            "sell",
                                            MERCHANT_TYPE_MERCHANT,
                                            item.name,
                                            item.quantity,
                                            PLAN_STATE_SKIPPED,
                                            (
                                                f"Blocked by {rule_reference}: "
                                                f"{MERCHANT_TYPE_LABELS[MERCHANT_TYPE_MERCHANT]} selector was not resolved in the current map."
                                            ),
                                            model_id=item.model_id,
                                        )
                                    )
                                continue

                            for item in destination_items:
                                plan.merchant_sell_item_ids.append(item.item_id)
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "sell",
                                        MERCHANT_TYPE_MERCHANT,
                                        item.name,
                                        item.quantity,
                                        PLAN_STATE_WILL_EXECUTE,
                                        "",
                                        model_id=item.model_id,
                                    )
                                )
                            continue

                        if destination == MERCHANT_TYPE_RUNE_TRADER:
                            rune_trader_coords = coords.get(MERCHANT_TYPE_RUNE_TRADER)
                            if rune_trader_coords is None:
                                for item in destination_items:
                                    plan.entries.append(
                                        ExecutionPlanEntry(
                                            "sell",
                                            MERCHANT_TYPE_RUNE_TRADER,
                                            item.name,
                                            item.quantity,
                                            PLAN_STATE_SKIPPED,
                                            (
                                                f"Blocked by {rule_reference}: "
                                                f"{MERCHANT_TYPE_LABELS[MERCHANT_TYPE_RUNE_TRADER]} selector was not resolved in the current map."
                                            ),
                                            model_id=item.model_id,
                                        )
                                    )
                                continue

                            for item in destination_items:
                                plan.rune_trader_sales.append(
                                    PlannedTraderSale(
                                        item_id=item.item_id,
                                        model_id=item.model_id,
                                        label=item.name,
                                    )
                                )
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "sell",
                                        MERCHANT_TYPE_RUNE_TRADER,
                                        item.name,
                                        item.quantity,
                                        PLAN_STATE_WILL_EXECUTE,
                                        "Standalone rune / insignia item.",
                                        model_id=item.model_id,
                                    )
                                )
                            continue

                        material_coords = coords.get(destination)
                        working_quantities = {
                            item.item_id: max(0, int(item.quantity))
                            for item in destination_items
                        }
                        material_sales: list[PlannedMaterialSale] = []
                        if material_coords is not None:
                            material_sales = self._plan_material_sales(destination_items, working_quantities, 0)

                        sold_quantities_by_item_id = {
                            sale.item_id: max(0, int(sale.quantity_to_sell))
                            for sale in material_sales
                        }
                        for sale in material_sales:
                            plan.material_sales.append(sale)
                            sale_reason = (
                                f"{sale.batches_to_sell} full trader batch(es) of {sale.batch_size}."
                                if int(sale.batch_size) > 1
                                else f"{sale.quantity_to_sell} individual trade(s)."
                            )
                            plan.entries.append(
                                ExecutionPlanEntry(
                                    "sell",
                                    sale.merchant_type,
                                    sale.label,
                                    sale.quantity_to_sell,
                                    PLAN_STATE_WILL_EXECUTE,
                                    sale_reason,
                                    model_id=sale.model_id,
                                )
                            )

                        for item in destination_items:
                            remaining_quantity = max(0, int(working_quantities.get(item.item_id, 0)))
                            if remaining_quantity <= 0:
                                continue

                            batch_size = max(1, int(self._get_material_batch_size(item.model_id)))
                            sold_quantity = sold_quantities_by_item_id.get(item.item_id, 0)
                            if destination == MERCHANT_TYPE_MATERIALS and remaining_quantity < batch_size:
                                merchant_coords = coords.get(MERCHANT_TYPE_MERCHANT)
                                merchant_reason = (
                                    "Merchant fallback after selling full trader batches; leftover common-material quantity is below the trader batch size."
                                    if sold_quantity > 0
                                    else "Merchant fallback because the common-material quantity is below the trader batch size."
                                )
                                if merchant_coords is None:
                                    plan.entries.append(
                                        ExecutionPlanEntry(
                                            "sell",
                                            MERCHANT_TYPE_MERCHANT,
                                            item.name,
                                            remaining_quantity,
                                            PLAN_STATE_SKIPPED,
                                            (
                                                f"Blocked by {rule_reference}: "
                                                f"{MERCHANT_TYPE_LABELS[MERCHANT_TYPE_MERCHANT]} selector was not resolved in the current map."
                                            ),
                                            model_id=item.model_id,
                                        )
                                    )
                                else:
                                    plan.merchant_sell_item_ids.append(item.item_id)
                                    plan.entries.append(
                                        ExecutionPlanEntry(
                                            "sell",
                                            MERCHANT_TYPE_MERCHANT,
                                            item.name,
                                            remaining_quantity,
                                            PLAN_STATE_WILL_EXECUTE,
                                            merchant_reason,
                                            model_id=item.model_id,
                                        )
                                    )
                                continue

                            if material_coords is None:
                                plan.entries.append(
                                    ExecutionPlanEntry(
                                        "sell",
                                        destination,
                                        item.name,
                                        remaining_quantity,
                                        PLAN_STATE_SKIPPED,
                                        (
                                            f"Blocked by {rule_reference}: "
                                            f"{MERCHANT_TYPE_LABELS[destination]} selector was not resolved in the current map."
                                        ),
                                        model_id=item.model_id,
                                    )
                                )
                                continue

                            keep_reason = (
                                f"Kept by {rule_reference}: {remaining_quantity} unit(s) remain after selling full trader batches."
                                if batch_size > 1
                                else f"Kept by {rule_reference}: {remaining_quantity} unit(s) remain after individual trades."
                            )
                            plan.entries.append(
                                ExecutionPlanEntry(
                                    "sell",
                                    destination,
                                    item.name,
                                    remaining_quantity,
                                    PLAN_STATE_SKIPPED,
                                    keep_reason,
                                    model_id=item.model_id,
                                )
                            )
                continue

        sim_model_counts = self._build_simulated_model_counts(items, plan)
        sim_inventory_items = self._get_items_after_planned_pre_buy_actions(items, plan)
        self._plan_buy_actions(
            plan,
            sim_model_counts,
            sim_inventory_items=sim_inventory_items,
            storage_items=storage_items,
        )
        self._plan_cleanup_actions(
            plan,
            sim_inventory_items,
            enabled_sell_rules,
            storage_open=storage_open,
            storage_context_available=storage_context_ready,
        )
        if projected_destination_context:
            self._apply_projected_preview_post_processing(plan, projected_target_outpost_name)
        plan.has_actions = bool(
            plan.destroy_actions
            or plan.destroy_item_ids
            or plan.merchant_stock_buys
            or plan.material_buys
            or plan.material_sales
            or plan.merchant_sell_item_ids
            or plan.rune_trader_sales
            or plan.rune_trader_buys
            or plan.storage_transfers
            or plan.cleanup_transfers
            or self._plan_needs_exact_storage_scan(plan)
        )
        self._log_plan_summary("Plan built", plan)
        self.last_plan_build_duration_ms = max(0.0, (time.perf_counter() - started_at) * 1000.0)
        return plan

    def _pause_inventory_plus(self):
        widget_handler = get_widget_handler()
        inv_widget = widget_handler.get_widget_info("Inventory Plus")
        if inv_widget is None:
            inv_widget = widget_handler.get_widget_info("InventoryPlus")
        if inv_widget and inv_widget.enabled and not inv_widget.is_paused:
            inv_widget.pause()
            return inv_widget
        return None

    def _wait_for_merchant_inventory(self, timeout_ms: int = 2500, step_ms: int = 10):
        waited = 0
        while waited < timeout_ms:
            offered_items = list(GLOBAL_CACHE.Trading.Merchant.GetOfferedItems())
            if offered_items:
                return offered_items
            waited += step_ms
            yield from Routines.Yield.wait(step_ms)
        return []

    def _open_merchant(self, coords: tuple[float, float]):
        x, y = coords
        self._debug_log(f"Opening merchant at {self._format_debug_coords(coords)}.")
        yield from Routines.Yield.Movement.FollowPath([(x, y)])
        yield from Routines.Yield.wait(100)
        ok = yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
        if not ok:
            self._debug_log(f"Merchant interaction failed at {self._format_debug_coords(coords)}.")
            return []
        yield from Routines.Yield.wait(700)
        offered_items = yield from self._wait_for_merchant_inventory()
        self._debug_log(f"Merchant interaction succeeded at {self._format_debug_coords(coords)}. offered_items={len(offered_items)}")
        return offered_items

    def _wait_for_action_queue_empty(
        self,
        queue_name: str,
        *,
        timeout_ms: int = 2000,
        step_ms: int = 50,
    ):
        waited_ms = 0
        while waited_ms <= max(0, int(timeout_ms)):
            if ActionQueueManager().IsEmpty(str(queue_name)):
                return True
            waited_ms += max(1, int(step_ms))
            yield from Routines.Yield.wait(step_ms)
        return bool(ActionQueueManager().IsEmpty(str(queue_name)))

    def _ensure_storage_open(self, *, purpose: str = "storage access"):
        storage_api = getattr(GLOBAL_CACHE, "Inventory", None)
        if self._is_storage_open():
            return True
        if storage_api is None or not callable(getattr(storage_api, "OpenXunlaiWindow", None)):
            self._debug_log(f"Xunlai API is unavailable while trying to open storage for {purpose}.")
            return False

        self._debug_log(f"Opening Xunlai for {purpose}.")
        storage_api.OpenXunlaiWindow()
        waited_ms = 0
        timeout_ms = 3000
        step_ms = 100
        while waited_ms <= timeout_ms:
            if self._is_storage_open():
                self._debug_log(f"Xunlai opened for {purpose}.")
                return True
            waited_ms += step_ms
            yield from Routines.Yield.wait(step_ms)
        self._debug_log(f"Failed to open Xunlai for {purpose} after {timeout_ms} ms.")
        return False

    def _get_inventory_stack_quantities(self, item_ids: list[int]) -> dict[int, int]:
        tracked_ids = {int(item_id) for item_id in item_ids if int(item_id) > 0}
        if not tracked_ids:
            return {}
        present_ids = set(self._get_inventory_item_ids())
        return {
            item_id: max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
            for item_id in tracked_ids
            if item_id in present_ids
        }

    def _wait_for_merchant_sell_confirmation(
        self,
        previous_quantities: dict[int, int],
        *,
        timeout_ms: int = MERCHANT_SELL_CONFIRM_TIMEOUT_MS,
        step_ms: int = 50,
    ):
        pending_item_ids = {int(item_id) for item_id in previous_quantities.keys() if int(item_id) > 0}
        confirmed_item_ids: set[int] = set()
        waited_ms = 0
        while pending_item_ids and waited_ms <= max(0, int(timeout_ms)):
            current_quantities = self._get_inventory_stack_quantities(list(pending_item_ids))
            for item_id in list(pending_item_ids):
                previous_quantity = max(0, int(previous_quantities.get(item_id, 0)))
                current_quantity = max(0, int(current_quantities.get(item_id, 0)))
                if current_quantity <= 0 or current_quantity < previous_quantity:
                    confirmed_item_ids.add(item_id)
                    pending_item_ids.discard(item_id)
            if not pending_item_ids:
                break
            waited_ms += max(1, int(step_ms))
            yield from Routines.Yield.wait(step_ms)
        return confirmed_item_ids, pending_item_ids

    def _wait_for_stack_quantity_target(
        self,
        item_id: int,
        expected_quantity: int,
        *,
        timeout_ms: int = DESTROY_CONFIRM_TIMEOUT_MS,
        step_ms: int = 50,
    ):
        waited_ms = 0
        safe_expected_quantity = max(0, int(expected_quantity))
        while waited_ms <= max(0, int(timeout_ms)):
            current_quantity = max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(int(item_id))))
            if current_quantity == safe_expected_quantity or current_quantity < safe_expected_quantity:
                return current_quantity
            waited_ms += max(1, int(step_ms))
            yield from Routines.Yield.wait(step_ms)
        return max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(int(item_id))))

    def _execute_destroy_phase(self, destroy_actions: list[PlannedDestroyAction] | list[int]) -> ExecutionPhaseOutcome:
        raw_destroy_actions = list(destroy_actions or [])
        tracked_item_ids = [
            int(action.item_id) if isinstance(action, PlannedDestroyAction) else int(action)
            for action in raw_destroy_actions
            if int(action.item_id if isinstance(action, PlannedDestroyAction) else action) > 0
        ]
        outcome = ExecutionPhaseOutcome(
            label="Destroy",
            measure_label="items",
            attempted=len(tracked_item_ids),
        )
        if not tracked_item_ids:
            return outcome

        pre_destroy_quantities = self._get_inventory_stack_quantities(tracked_item_ids)
        normalized_actions: list[PlannedDestroyAction] = []
        for raw_action in raw_destroy_actions:
            if isinstance(raw_action, PlannedDestroyAction):
                normalized_actions.append(raw_action)
                continue
            safe_item_id = int(raw_action)
            previous_quantity = max(0, int(pre_destroy_quantities.get(safe_item_id, 0)))
            normalized_actions.append(
                PlannedDestroyAction(
                    item_id=safe_item_id,
                    model_id=0,
                    label=f"Item {safe_item_id}",
                    quantity_to_destroy=previous_quantity,
                    source_quantity=previous_quantity,
                )
            )

        destroy_queue = sorted(
            normalized_actions,
            key=lambda action: (
                1 if bool(action.requires_split) else 0,
                str(action.label or "").lower(),
                int(action.item_id),
            ),
        )

        missing_item_count = max(0, len(tracked_item_ids) - len(pre_destroy_quantities))
        if missing_item_count > 0:
            outcome.depleted += missing_item_count

        self._debug_log(
            f"Destroy phase: planned_items={len(tracked_item_ids)} present_items={len(pre_destroy_quantities)}"
        )
        for action in destroy_queue:
            item_id = int(action.item_id)
            previous_quantity = max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
            if previous_quantity <= 0:
                previous_quantity = max(0, int(pre_destroy_quantities.get(item_id, 0)))
            if previous_quantity <= 0:
                continue

            planned_destroy_quantity = max(0, int(action.quantity_to_destroy))
            planned_keep_quantity = max(0, int(action.keep_quantity))
            if planned_destroy_quantity <= 0:
                continue

            if bool(action.requires_split):
                split_destination = self._find_inventory_empty_slot()
                if split_destination is None:
                    outcome.timeout_failures += 1
                    self._debug_log(
                        f"Destroy split skipped: item_id={item_id} keep={planned_keep_quantity} destroy={planned_destroy_quantity} "
                        "no empty slot was available at execution time."
                    )
                    continue

                expected_source_quantity = max(0, previous_quantity - planned_keep_quantity)
                GLOBAL_CACHE.Inventory.MoveItem(
                    item_id,
                    int(split_destination.bag_id),
                    int(split_destination.slot),
                    planned_keep_quantity,
                )
                updated_quantity = yield from self._wait_for_stack_quantity_target(
                    item_id,
                    expected_source_quantity,
                    timeout_ms=DESTROY_CONFIRM_TIMEOUT_MS,
                    step_ms=50,
                )
                if updated_quantity != expected_source_quantity or updated_quantity != planned_destroy_quantity:
                    outcome.timeout_failures += 1
                    self._debug_log(
                        f"Destroy split verification failed: item_id={item_id} expected={planned_destroy_quantity} "
                        f"observed={updated_quantity} keep={planned_keep_quantity}"
                    )
                    continue
                previous_quantity = updated_quantity

            if previous_quantity != planned_destroy_quantity:
                outcome.timeout_failures += 1
                self._debug_log(
                    f"Destroy quantity mismatch: item_id={item_id} planned={planned_destroy_quantity} current={previous_quantity}"
                )
                continue

            GLOBAL_CACHE.Inventory.DestroyItem(int(item_id))
            confirmed_item_ids, pending_item_ids = yield from self._wait_for_merchant_sell_confirmation(
                {int(item_id): previous_quantity},
                timeout_ms=DESTROY_CONFIRM_TIMEOUT_MS,
                step_ms=50,
            )
            if confirmed_item_ids:
                outcome.completed += 1
            else:
                outcome.timeout_failures += len(pending_item_ids) or 1
            yield from Routines.Yield.wait(40)

        self._debug_log(
            f"Destroy phase completed: completed={outcome.completed}/{outcome.attempted} "
            f"timeouts={outcome.timeout_failures} depleted={outcome.depleted}"
        )
        return outcome

    def _buy_merchant_model(self, model_id: int, quantity: int):
        if quantity <= 0:
            return False
        offered_items = list(GLOBAL_CACHE.Trading.Merchant.GetOfferedItems())
        matched_item_id = 0
        for offered_item_id in offered_items:
            if int(GLOBAL_CACHE.Item.GetModelID(offered_item_id)) == int(model_id):
                matched_item_id = int(offered_item_id)
                break
        if matched_item_id <= 0:
            self._debug_log(f"Merchant stock buy skipped: model={model_id} quantity={quantity} was not offered.")
            return False

        buy_price = int(GLOBAL_CACHE.Item.Properties.GetValue(matched_item_id)) * 2
        self._debug_log(
            f"Merchant stock buy: model={model_id} matched_item_id={matched_item_id} "
            f"quantity={quantity} buy_price={buy_price}"
        )
        for _ in range(max(0, int(quantity))):
            GLOBAL_CACHE.Trading.Merchant.BuyItem(matched_item_id, buy_price)

        while not ActionQueueManager().IsEmpty("MERCHANT"):
            yield from Routines.Yield.wait(50)
        self._debug_log(f"Merchant stock buy completed: model={model_id} quantity={quantity}")
        return True

    def _buy_planned_materials(
        self,
        coords: tuple[float, float],
        material_buys: list[PlannedMaterialBuy],
        *,
        phase_label: str = "Material buys",
    ) -> ExecutionPhaseOutcome:
        outcome = ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="trades",
            attempted=sum(
                max(0, int(planned_buy.quantity)) // max(1, int(planned_buy.batch_size))
                for planned_buy in material_buys
            ),
        )
        if not material_buys:
            return outcome

        self._debug_log(
            f"{phase_label}: coords={self._format_debug_coords(coords)} planned_targets={len(material_buys)} "
            f"planned_units={sum(max(0, int(buy.quantity)) for buy in material_buys)}"
        )
        x, y = coords
        trader_items = yield from Routines.Yield.Merchant._interact_with_trader_xy(  # pylint: disable=protected-access
            x,
            y,
            inventory_timeout_ms=2500,
            inventory_step_ms=10,
        )
        if not trader_items:
            ConsoleLog(MODULE_NAME, f"{phase_label} inventory did not load.", Console.MessageType.Warning)
            outcome.load_failures += 1
            self._debug_log(f"{phase_label}: trader inventory failed to load at {self._format_debug_coords(coords)}.")
            return outcome

        for planned_buy in material_buys:
            trader_item_id = 0
            for candidate in trader_items:
                if int(GLOBAL_CACHE.Item.GetModelID(candidate)) == int(planned_buy.model_id):
                    trader_item_id = int(candidate)
                    break
            if trader_item_id <= 0:
                outcome.unavailable += 1
                ConsoleLog(
                    MODULE_NAME,
                    f"Crafting material target {planned_buy.model_id} was not offered by the trader.",
                    Console.MessageType.Warning,
                )
                continue

            transactions = max(0, int(planned_buy.quantity) // max(1, int(planned_buy.batch_size)))
            for _ in range(transactions):
                character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                quoted_value = yield from Routines.Yield.Merchant._wait_for_quote(  # pylint: disable=protected-access
                    GLOBAL_CACHE.Trading.Trader.RequestQuote,
                    trader_item_id,
                    timeout_ms=750,
                    step_ms=10,
                )
                if quoted_value <= 0:
                    outcome.quote_failures += 1
                    break
                if character_gold < quoted_value:
                    outcome.gold_blocked += 1
                    break

                GLOBAL_CACHE.Trading.Trader.BuyItem(trader_item_id, quoted_value)
                completed = yield from Routines.Yield.Merchant._wait_for_transaction(  # pylint: disable=protected-access
                    timeout_ms=750,
                    step_ms=10,
                )
                if not completed:
                    outcome.timeout_failures += 1
                    break
                outcome.completed += 1
                yield from Routines.Yield.wait(40)

        self._debug_log(
            f"{phase_label}: completed={outcome.completed}/{outcome.attempted} quote_failures={outcome.quote_failures} "
            f"timeouts={outcome.timeout_failures} unavailable_targets={outcome.unavailable} "
            f"gold_blocked={outcome.gold_blocked} load_failures={outcome.load_failures}"
        )
        return outcome

    def _sell_planned_materials(
        self,
        coords: tuple[float, float],
        material_sales: list[PlannedMaterialSale],
        *,
        phase_label: str = "Material sales",
    ) -> ExecutionPhaseOutcome:
        outcome = ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="trades",
            attempted=sum(max(0, int(sale.batches_to_sell)) for sale in material_sales),
        )
        if not material_sales:
            return outcome

        self._debug_log(
            f"{phase_label}: coords={self._format_debug_coords(coords)} "
            f"sale_stacks={len(material_sales)} planned_trades={sum(max(0, int(sale.batches_to_sell)) for sale in material_sales)}"
        )
        x, y = coords
        trader_items = yield from Routines.Yield.Merchant._interact_with_trader_xy(  # pylint: disable=protected-access
            x,
            y,
            inventory_timeout_ms=2500,
            inventory_step_ms=10,
        )
        if not trader_items:
            ConsoleLog(MODULE_NAME, "Material trader inventory did not load.", Console.MessageType.Warning)
            outcome.load_failures += 1
            self._debug_log(f"{phase_label}: trader inventory failed to load at {self._format_debug_coords(coords)}.")
            return outcome

        for sale in material_sales:
            for _ in range(max(0, int(sale.batches_to_sell))):
                previous_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(sale.item_id))
                if previous_quantity < sale.batch_size:
                    outcome.depleted += 1
                    break

                quoted_value = yield from Routines.Yield.Merchant._wait_for_quote(  # pylint: disable=protected-access
                    GLOBAL_CACHE.Trading.Trader.RequestSellQuote,
                    sale.item_id,
                    timeout_ms=350,
                    step_ms=10,
                )
                if quoted_value <= 0:
                    outcome.quote_failures += 1
                    break

                GLOBAL_CACHE.Trading.Trader.SellItem(sale.item_id, quoted_value)
                updated_quantity = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(  # pylint: disable=protected-access
                    sale.item_id,
                    previous_quantity,
                    timeout_ms=350,
                    step_ms=10,
                )
                if updated_quantity >= previous_quantity:
                    outcome.timeout_failures += 1
                    break
                outcome.completed += 1
                yield from Routines.Yield.wait(40)
        self._debug_log(
            f"{phase_label}: completed={outcome.completed}/{outcome.attempted} quote_failures={outcome.quote_failures} "
            f"quantity_failures={outcome.timeout_failures} depleted={outcome.depleted} load_failures={outcome.load_failures}"
        )
        return outcome

    def _sell_planned_trader_items(
        self,
        coords: tuple[float, float],
        trader_sales: list[PlannedTraderSale],
        *,
        phase_label: str = "Rune trader sales",
    ) -> ExecutionPhaseOutcome:
        outcome = ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=len(trader_sales),
        )
        if not trader_sales:
            return outcome

        self._debug_log(
            f"{phase_label}: coords={self._format_debug_coords(coords)} planned_items={len(trader_sales)}"
        )
        x, y = coords
        trader_items = yield from Routines.Yield.Merchant._interact_with_trader_xy(  # pylint: disable=protected-access
            x,
            y,
            inventory_timeout_ms=2500,
            inventory_step_ms=10,
        )
        if not trader_items:
            ConsoleLog(MODULE_NAME, "Rune trader inventory did not load.", Console.MessageType.Warning)
            outcome.load_failures += 1
            self._debug_log(f"{phase_label}: trader inventory failed to load at {self._format_debug_coords(coords)}.")
            return outcome

        for sale in trader_sales:
            previous_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(sale.item_id))
            if previous_quantity <= 0:
                outcome.depleted += 1
                continue

            quoted_value = yield from Routines.Yield.Merchant._wait_for_quote(  # pylint: disable=protected-access
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote,
                sale.item_id,
                timeout_ms=350,
                step_ms=10,
            )
            if quoted_value <= 0:
                outcome.quote_failures += 1
                continue

            GLOBAL_CACHE.Trading.Trader.SellItem(sale.item_id, quoted_value)
            updated_quantity = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(  # pylint: disable=protected-access
                sale.item_id,
                previous_quantity,
                timeout_ms=350,
                step_ms=10,
            )
            if updated_quantity >= previous_quantity:
                outcome.timeout_failures += 1
                continue
            outcome.completed += 1
            yield from Routines.Yield.wait(40)
        self._debug_log(
            f"{phase_label}: completed={outcome.completed}/{outcome.attempted} quote_failures={outcome.quote_failures} "
            f"quantity_failures={outcome.timeout_failures} depleted={outcome.depleted} load_failures={outcome.load_failures}"
        )
        return outcome

    def _execute_storage_transfers(
        self,
        storage_transfers: list[PlannedStorageTransfer],
        *,
        phase_label: str = "Storage transfers",
    ) -> ExecutionPhaseOutcome:
        normalized_transfers = [
            transfer
            for transfer in storage_transfers
            if int(transfer.item_id) > 0 and max(0, int(transfer.quantity)) > 0
        ]
        outcome = ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=sum(max(0, int(transfer.quantity)) for transfer in normalized_transfers),
        )
        if not normalized_transfers:
            return outcome

        self._debug_log(
            f"{phase_label}: transfers={len(normalized_transfers)} "
            f"planned_items={sum(max(0, int(transfer.quantity)) for transfer in normalized_transfers)}"
        )
        for transfer in normalized_transfers:
            item_id = int(transfer.item_id)
            quantity = max(0, int(transfer.quantity))
            if quantity <= 0:
                continue

            current_quantity = max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
            if current_quantity <= 0:
                outcome.depleted += quantity
                continue
            requested_quantity = min(current_quantity, quantity)
            depleted_quantity = max(0, quantity - current_quantity)
            if requested_quantity <= 0:
                outcome.depleted += quantity
                continue

            moved = False
            if transfer.direction == STORAGE_TRANSFER_WITHDRAW:
                moved = bool(GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(item_id, ammount=requested_quantity))
            elif transfer.direction == STORAGE_TRANSFER_DEPOSIT:
                moved = bool(GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id, ammount=requested_quantity))

            if not moved:
                outcome.timeout_failures += requested_quantity
                outcome.depleted += depleted_quantity
                continue

            queue_cleared = yield from self._wait_for_action_queue_empty("ACTION", timeout_ms=2000, step_ms=50)
            final_quantity = max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
            if queue_cleared:
                expected_quantity = max(0, current_quantity - requested_quantity)
                final_quantity = yield from self._wait_for_stack_quantity_target(
                    item_id,
                    expected_quantity,
                    timeout_ms=2000,
                    step_ms=50,
                )

            moved_quantity = max(0, current_quantity - max(0, int(final_quantity)))
            if moved_quantity > 0:
                outcome.completed += moved_quantity
            shortfall = max(0, requested_quantity - moved_quantity)
            if shortfall > 0:
                outcome.timeout_failures += shortfall
            outcome.depleted += depleted_quantity
            yield from Routines.Yield.wait(60)

        self._debug_log(
            f"{phase_label}: completed={outcome.completed}/{outcome.attempted} "
            f"timeouts={outcome.timeout_failures} depleted={outcome.depleted}"
        )
        return outcome

    def _buy_planned_rune_trader_items(
        self,
        coords: tuple[float, float],
        rune_buys: list[PlannedTraderBuy],
        *,
        phase_label: str = "Rune trader buys",
    ) -> ExecutionPhaseOutcome:
        outcome = ExecutionPhaseOutcome(
            label=phase_label,
            measure_label="items",
            attempted=sum(max(0, int(planned_buy.quantity)) for planned_buy in rune_buys),
        )
        if not rune_buys:
            return outcome

        self._debug_log(
            f"{phase_label}: coords={self._format_debug_coords(coords)} "
            f"planned_targets={len(rune_buys)} planned_items={outcome.attempted}"
        )
        x, y = coords
        trader_items = yield from Routines.Yield.Merchant._interact_with_trader_xy(  # pylint: disable=protected-access
            x,
            y,
            inventory_timeout_ms=2500,
            inventory_step_ms=10,
        )
        if not trader_items:
            ConsoleLog(MODULE_NAME, f"{phase_label} inventory did not load.", Console.MessageType.Warning)
            outcome.load_failures += 1
            self._debug_log(f"{phase_label}: trader inventory failed to load at {self._format_debug_coords(coords)}.")
            return outcome

        for planned_buy in rune_buys:
            safe_identifier = _normalize_rune_identifier(planned_buy.identifier)
            if not safe_identifier:
                continue

            trader_item_id = 0
            for candidate in trader_items:
                candidate_identifiers = self._get_standalone_rune_identifiers_for_item_id(int(candidate))
                if safe_identifier in candidate_identifiers:
                    trader_item_id = int(candidate)
                    break
            if trader_item_id <= 0:
                outcome.unavailable += max(0, int(planned_buy.quantity))
                ConsoleLog(
                    MODULE_NAME,
                    f"{planned_buy.label} was not offered by the Rune Trader.",
                    Console.MessageType.Warning,
                )
                continue

            for _ in range(max(0, int(planned_buy.quantity))):
                character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                quoted_value = yield from Routines.Yield.Merchant._wait_for_quote(  # pylint: disable=protected-access
                    GLOBAL_CACHE.Trading.Trader.RequestQuote,
                    trader_item_id,
                    timeout_ms=750,
                    step_ms=10,
                )
                if quoted_value <= 0:
                    outcome.quote_failures += 1
                    break
                if character_gold < quoted_value:
                    outcome.gold_blocked += 1
                    break

                GLOBAL_CACHE.Trading.Trader.BuyItem(trader_item_id, quoted_value)
                completed = yield from Routines.Yield.Merchant._wait_for_transaction(  # pylint: disable=protected-access
                    timeout_ms=750,
                    step_ms=10,
                )
                if not completed:
                    outcome.timeout_failures += 1
                    break
                outcome.completed += 1
                yield from Routines.Yield.wait(40)

        self._debug_log(
            f"{phase_label}: completed={outcome.completed}/{outcome.attempted} "
            f"unavailable={outcome.unavailable} quote_failures={outcome.quote_failures} "
            f"timeouts={outcome.timeout_failures} gold_blocked={outcome.gold_blocked} "
            f"load_failures={outcome.load_failures}"
        )
        return outcome

    def _format_execution_phase_summary(self, outcome: ExecutionPhaseOutcome) -> str:
        if (
            outcome.attempted <= 0
            and outcome.completed <= 0
            and outcome.unavailable <= 0
            and outcome.quote_failures <= 0
            and outcome.timeout_failures <= 0
            and outcome.load_failures <= 0
            and outcome.gold_blocked <= 0
            and outcome.depleted <= 0
        ):
            return ""

        parts: list[str] = []
        if outcome.attempted > 0:
            parts.append(f"{outcome.completed}/{outcome.attempted} {outcome.measure_label}")
        elif outcome.completed > 0:
            parts.append(f"{outcome.completed} {outcome.measure_label}")
        if outcome.unavailable > 0:
            parts.append(f"{outcome.unavailable} unavailable")
        if outcome.quote_failures > 0:
            parts.append(f"{outcome.quote_failures} quote failure(s)")
        if outcome.timeout_failures > 0:
            parts.append(f"{outcome.timeout_failures} timeout(s)")
        if outcome.load_failures > 0:
            parts.append(f"{outcome.load_failures} inventory load failure(s)")
        if outcome.gold_blocked > 0:
            parts.append(f"{outcome.gold_blocked} blocked by gold")
        if outcome.depleted > 0:
            parts.append(f"{outcome.depleted} depleted")
        return f"{outcome.label}: {', '.join(parts)}."

    def _open_xunlai_and_scan_preview(self):
        self.storage_scan_running = True
        self.last_error = ""
        try:
            if bool(GLOBAL_CACHE.Inventory.IsStorageOpen()):
                self._scan_preview()
                self.status_message = "Exact storage scan complete. Preview refreshed with Xunlai counts."
                return

            self.status_message = "Opening Xunlai for exact storage scan..."
            opened = yield from self._ensure_storage_open(purpose="exact storage preview scan")
            if not opened:
                self.status_message = "Could not open Xunlai for exact storage scan."
                return

            yield from Routines.Yield.wait(150)
            self._scan_preview()
            self.status_message = "Exact storage scan complete. Preview refreshed with Xunlai counts."
        except Exception as exc:
            self.last_error = f"{exc}"
            self.status_message = "Exact storage scan failed. See the console log for details."
            ConsoleLog(MODULE_NAME, f"Exact storage scan error: {exc}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, traceback.format_exc(), Console.MessageType.Error)
        finally:
            self.storage_scan_running = False
            yield

    def _scan_preview(self):
        self._invalidate_supported_context_cache()
        projected_target_outpost_id, projected_target_outpost_name = self._get_preview_projection_target()
        self.preview_plan = self._build_plan(projected_preview=True)
        self.preview_ready = True
        self._set_preview_projection_state(
            requires_travel=projected_target_outpost_id > 0,
            target_outpost_id=projected_target_outpost_id,
            target_outpost_name=projected_target_outpost_name,
        )
        self._clear_preview_inventory_diff()
        if self._preview_has_execute_travel_pending():
            if self.preview_plan.has_actions:
                self.status_message = (
                    f"Projected preview complete. Travel + Execute will travel to {projected_target_outpost_name}, "
                    "rebuild live, and then run the merchant plan. Execute Here can still run any green local entries."
                )
            else:
                self.status_message = (
                    f"Projected preview complete. Travel + Execute will still travel to {projected_target_outpost_name}, "
                    "but no merchant work is currently projected."
                )
        elif self.preview_plan.has_actions:
            self.status_message = "Preview complete. Review the plan, then run Travel + Execute or Execute Here when ready."
        else:
            self.status_message = "Preview complete. No actionable merchant work was found."
        self.last_error = ""

    def _travel_and_preview_only(self):
        self.travel_preview_running = True
        self.last_error = ""
        self.last_execution_summary = ""
        try:
            target_outpost_id = max(0, int(self.target_outpost_id)) if self.auto_travel_enabled else 0
            target_outpost_name = self._get_outpost_name(target_outpost_id) if target_outpost_id > 0 else ""
            self._debug_log(
                f"Travel + Preview start: auto_travel={self.auto_travel_enabled} "
                f"target={target_outpost_name} ({target_outpost_id})"
            )
            if target_outpost_id > 0 and not self._is_travel_target_reached(target_outpost_id):
                self.status_message = f"Traveling to {target_outpost_name} for preview."
                travel_ok = yield from self._travel_to_target_outpost(target_outpost_id)
                if not travel_ok:
                    self.status_message = f"Failed to travel to {target_outpost_name} for preview."
                    self._debug_log(f"Travel + Preview failed to reach {target_outpost_name} ({target_outpost_id}).")
                    return
                self._debug_log(f"Travel + Preview reached {target_outpost_name} ({target_outpost_id}).")
                yield from Routines.Yield.wait(300)

            self._invalidate_supported_context_cache()
            self.preview_plan = self._build_plan()
            self.preview_ready = True
            self._clear_preview_projection_state()
            self._clear_preview_inventory_diff()
            if self.preview_plan.travel_to_outpost_id > 0:
                self.status_message = "Travel preview completed, but the target outpost still needs to be reached."
            elif self.preview_plan.has_actions:
                self.status_message = "Travel and preview complete. Review the refreshed merchant plan."
            else:
                self.status_message = "Travel and preview complete. No actionable merchant work was found."
        except Exception as exc:
            self.last_error = f"{exc}"
            self.status_message = "Travel + Preview failed. See the console log for details."
            ConsoleLog(MODULE_NAME, f"Travel + Preview error: {exc}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, traceback.format_exc(), Console.MessageType.Error)
        finally:
            self.travel_preview_running = False
            yield

    def _execute_merchant_sell_phase(
        self,
        merchant_coords: tuple[float, float] | None,
        merchant_sell_item_ids: list[int],
    ) -> ExecutionPhaseOutcome:
        outcome = ExecutionPhaseOutcome(
            label="Merchant sells",
            measure_label="items",
            attempted=len(merchant_sell_item_ids),
        )
        if not merchant_coords or not merchant_sell_item_ids:
            return outcome

        self._debug_log(
            f"Merchant sell phase: coords={self._format_debug_coords(merchant_coords)} "
            f"item_count={len(merchant_sell_item_ids)}"
        )
        merchant_items = yield from self._open_merchant(merchant_coords)
        if not merchant_items:
            outcome.load_failures += 1
            ConsoleLog(MODULE_NAME, "Merchant inventory did not load for merchant-sell actions.", Console.MessageType.Warning)
            self._debug_log("Merchant sell phase: inventory did not load.")
            return outcome

        pre_sell_quantities = self._get_inventory_stack_quantities(merchant_sell_item_ids)
        sell_item_ids = list(pre_sell_quantities.keys())
        missing_item_count = max(0, len(merchant_sell_item_ids) - len(sell_item_ids))
        if missing_item_count > 0:
            outcome.depleted += missing_item_count
        if not sell_item_ids:
            self._debug_log("Merchant sell phase skipped send because planned item ids were no longer in inventory.")
            return outcome

        yield from Routines.Yield.Merchant.SellItems(sell_item_ids)
        confirmed_ids, pending_ids = yield from self._wait_for_merchant_sell_confirmation(pre_sell_quantities)
        outcome.completed = len(confirmed_ids)
        outcome.timeout_failures += len(pending_ids)
        if pending_ids:
            ConsoleLog(
                MODULE_NAME,
                f"Merchant sell verification timed out for {len(pending_ids)} item(s) after SellItems.",
                Console.MessageType.Warning,
            )
        self._debug_log(
            f"Merchant sell phase completed: confirmed={len(confirmed_ids)} pending={len(pending_ids)} "
            f"missing_before_send={missing_item_count}"
        )
        return outcome

    def _execute_now(self, *, local_only: bool = False):
        self.execution_running = True
        self.last_error = ""
        self.last_execution_summary = ""
        self.last_cleanup_summary = ""
        self.last_execution_phase_durations_ms = {}
        self._clear_preview_inventory_diff()
        paused_inventory_plus = None
        phase_summaries: list[str] = []
        try:
            self._invalidate_supported_context_cache()
            self._clear_preview_projection_state()
            execution_label = "Execute Here" if local_only else "Travel + Execute"
            plan = self._build_plan(ignore_travel_target=local_only)
            self.preview_plan = plan
            local_availability = self._get_preview_here_availability()
            actionable_here_count, skipped_here_count = self._get_locally_actionable_preview_counts(
                plan,
                availability_here=local_availability,
            )
            self._log_plan_summary(f"{execution_label} start", plan)
            if plan.travel_to_outpost_id > 0:
                self.status_message = f"Traveling to {plan.travel_to_outpost_name} before merchant handling."
                self._debug_log(
                    f"Execution travel: target={plan.travel_to_outpost_name} ({plan.travel_to_outpost_id})"
                )
                travel_ok = yield from self._travel_to_target_outpost(plan.travel_to_outpost_id)
                if not travel_ok:
                    self.status_message = f"Failed to travel to {plan.travel_to_outpost_name}."
                    self._debug_log(
                        f"Execution aborted: failed to travel to {plan.travel_to_outpost_name} ({plan.travel_to_outpost_id})."
                    )
                    return
                self._invalidate_supported_context_cache()
                yield from Routines.Yield.wait(300)
                plan = self._build_plan()
                self.preview_plan = plan
                local_availability = self._get_preview_here_availability()
                actionable_here_count, skipped_here_count = self._get_locally_actionable_preview_counts(
                    plan,
                    availability_here=local_availability,
                )
                self._clear_preview_projection_state()
                self._log_plan_summary("Execution post-travel plan", plan)
            if not plan.supported_map:
                if not self._plan_has_local_destroy_actions(plan) and not self._plan_has_local_storage_actions(plan):
                    self.status_message = plan.supported_reason
                    self._debug_log(f"Execution aborted: unsupported map. {plan.supported_reason}")
                    return
                if self._plan_has_local_destroy_actions(plan) and self._plan_has_local_storage_actions(plan):
                    self._debug_log(
                        f"Execution continuing with local destroy actions and Xunlai cleanup on unsupported map. {plan.supported_reason}"
                    )
                elif self._plan_has_local_destroy_actions(plan):
                    self._debug_log(
                        f"Execution continuing with local destroy actions on unsupported map. {plan.supported_reason}"
                    )
                else:
                    self._debug_log(
                        f"Execution continuing with Xunlai cleanup on unsupported map. {plan.supported_reason}"
                    )
            storage_scan_failed = False
            storage_available_here = bool(local_availability.get(MERCHANT_TYPE_STORAGE, False))
            if self._plan_needs_exact_storage_scan(plan):
                storage_opened = False
                if local_only and not storage_available_here:
                    storage_scan_failed = True
                    phase_summaries.append("Rune trader buys were skipped because Xunlai is not available here.")
                else:
                    self.status_message = "Opening Xunlai for exact storage-aware execution."
                    storage_opened = yield from self._ensure_storage_open(purpose="storage-aware execution")
                if storage_opened:
                    yield from Routines.Yield.wait(150)
                    self._invalidate_supported_context_cache()
                    plan = self._build_plan(ignore_travel_target=local_only)
                    self.preview_plan = plan
                    local_availability = self._get_preview_here_availability()
                    actionable_here_count, skipped_here_count = self._get_locally_actionable_preview_counts(
                        plan,
                        availability_here=local_availability,
                    )
                    storage_available_here = bool(local_availability.get(MERCHANT_TYPE_STORAGE, False))
                    self._clear_preview_projection_state()
                    self._log_plan_summary("Execution storage-refreshed plan", plan)
                elif not storage_scan_failed:
                    storage_scan_failed = True
                    phase_summaries.append("Storage-aware rune planning was skipped because Xunlai could not be opened.")
                    ConsoleLog(
                        MODULE_NAME,
                        "Could not open Xunlai for exact storage-aware execution; continuing with other runnable actions.",
                        Console.MessageType.Warning,
                    )
                    has_other_runnable_actions = bool(
                        plan.destroy_actions
                        or plan.destroy_item_ids
                        or plan.merchant_stock_buys
                        or plan.material_buys
                        or plan.material_sales
                        or plan.merchant_sell_item_ids
                        or plan.rune_trader_sales
                    )
                    if not has_other_runnable_actions:
                        self.status_message = "Could not open Xunlai for exact storage-aware execution."
                        self._debug_log("Execution aborted: exact storage-aware rune planning required Xunlai, but it could not be opened.")
                        return
            if not plan.has_actions:
                if storage_scan_failed:
                    self.status_message = "Could not open Xunlai for exact storage-aware execution."
                else:
                    self.status_message = "Nothing to execute for the current rules and inventory state."
                self._debug_log("Execution aborted: no actionable work in the current plan.")
                return

            paused_inventory_plus = self._pause_inventory_plus()
            if paused_inventory_plus is not None:
                self._debug_log("Execution: paused Inventory Plus for merchant handling.")

            merchant_coords = plan.coords.get(MERCHANT_TYPE_MERCHANT)
            destroy_started_at = time.perf_counter()
            destroy_outcome = yield from self._execute_destroy_phase(plan.destroy_actions or plan.destroy_item_ids)
            self.last_execution_phase_durations_ms["destroys"] = max(0.0, (time.perf_counter() - destroy_started_at) * 1000.0)
            destroy_summary = self._format_execution_phase_summary(destroy_outcome)
            if destroy_summary:
                phase_summaries.append(destroy_summary)

            material_coords = plan.coords.get(MERCHANT_TYPE_MATERIALS)
            common_material_sales = [sale for sale in plan.material_sales if sale.merchant_type == MERCHANT_TYPE_MATERIALS]
            material_sale_outcome = ExecutionPhaseOutcome(label="Material sales", measure_label="trades")
            material_sales_started_at = time.perf_counter()
            if material_coords and common_material_sales:
                material_sale_outcome = yield from self._sell_planned_materials(
                    material_coords,
                    common_material_sales,
                    phase_label="Material sales",
                )
            self.last_execution_phase_durations_ms["material_sales"] = max(0.0, (time.perf_counter() - material_sales_started_at) * 1000.0)
            material_sale_summary = self._format_execution_phase_summary(material_sale_outcome)
            if material_sale_summary:
                phase_summaries.append(material_sale_summary)

            rare_material_coords = plan.coords.get(MERCHANT_TYPE_RARE_MATERIALS)
            rare_material_sales = [sale for sale in plan.material_sales if sale.merchant_type == MERCHANT_TYPE_RARE_MATERIALS]
            rare_material_sale_outcome = ExecutionPhaseOutcome(label="Rare material sales", measure_label="trades")
            rare_material_sales_started_at = time.perf_counter()
            if rare_material_coords and rare_material_sales:
                rare_material_sale_outcome = yield from self._sell_planned_materials(
                    rare_material_coords,
                    rare_material_sales,
                    phase_label="Rare material sales",
                )
            self.last_execution_phase_durations_ms["rare_material_sales"] = max(0.0, (time.perf_counter() - rare_material_sales_started_at) * 1000.0)
            rare_material_sale_summary = self._format_execution_phase_summary(rare_material_sale_outcome)
            if rare_material_sale_summary:
                phase_summaries.append(rare_material_sale_summary)

            merchant_sell_started_at = time.perf_counter()
            merchant_sell_outcome = yield from self._execute_merchant_sell_phase(merchant_coords, plan.merchant_sell_item_ids)
            self.last_execution_phase_durations_ms["merchant_sells"] = max(0.0, (time.perf_counter() - merchant_sell_started_at) * 1000.0)
            merchant_sell_summary = self._format_execution_phase_summary(merchant_sell_outcome)
            if merchant_sell_summary:
                phase_summaries.append(merchant_sell_summary)

            rune_trader_coords = plan.coords.get(MERCHANT_TYPE_RUNE_TRADER)
            rune_sale_outcome = ExecutionPhaseOutcome(label="Rune trader sales", measure_label="items")
            rune_sales_started_at = time.perf_counter()
            if rune_trader_coords and plan.rune_trader_sales:
                rune_sale_outcome = yield from self._sell_planned_trader_items(
                    rune_trader_coords,
                    plan.rune_trader_sales,
                    phase_label="Rune trader sales",
                )
            self.last_execution_phase_durations_ms["rune_sales"] = max(0.0, (time.perf_counter() - rune_sales_started_at) * 1000.0)
            rune_sale_summary = self._format_execution_phase_summary(rune_sale_outcome)
            if rune_sale_summary:
                phase_summaries.append(rune_sale_summary)

            storage_withdraw_transfers = [
                transfer
                for transfer in plan.storage_transfers
                if str(transfer.direction) == STORAGE_TRANSFER_WITHDRAW
            ]
            storage_transfer_outcome = ExecutionPhaseOutcome(label="Storage withdraws", measure_label="items")
            storage_transfers_started_at = time.perf_counter()
            storage_transfer_ready = not bool(storage_withdraw_transfers)
            if storage_withdraw_transfers:
                storage_ready = self._is_storage_open()
                if not storage_ready and local_only and not storage_available_here:
                    storage_transfer_outcome.load_failures += 1
                    phase_summaries.append("Rune trader buys were skipped because Xunlai is not available here.")
                    plan.rune_trader_buys = []
                elif not storage_ready:
                    storage_ready = yield from self._ensure_storage_open(purpose="planned storage transfers")
                if storage_ready:
                    storage_transfer_ready = True
                    storage_transfer_outcome = yield from self._execute_storage_transfers(
                        storage_withdraw_transfers,
                        phase_label="Storage withdraws",
                    )
                    yield from Routines.Yield.wait(100)
                    self._invalidate_supported_context_cache()
                    plan = self._build_plan(ignore_travel_target=local_only)
                    self.preview_plan = plan
                    local_availability = self._get_preview_here_availability()
                    actionable_here_count, skipped_here_count = self._get_locally_actionable_preview_counts(
                        plan,
                        availability_here=local_availability,
                    )
                    storage_available_here = bool(local_availability.get(MERCHANT_TYPE_STORAGE, False))
                    self._clear_preview_projection_state()
                    self._log_plan_summary("Execution post-storage plan", plan)
                    rune_trader_coords = plan.coords.get(MERCHANT_TYPE_RUNE_TRADER)
                else:
                    storage_transfer_outcome.load_failures += 1
                    ConsoleLog(
                        MODULE_NAME,
                        "Could not open Xunlai for planned storage transfers.",
                        Console.MessageType.Warning,
                    )
                    phase_summaries.append("Rune trader buys were skipped because planned Xunlai transfers could not be completed.")
                    plan.rune_trader_buys = []
            self.last_execution_phase_durations_ms["storage_transfers"] = max(0.0, (time.perf_counter() - storage_transfers_started_at) * 1000.0)
            storage_transfer_summary = self._format_execution_phase_summary(storage_transfer_outcome)
            if storage_transfer_summary:
                phase_summaries.append(storage_transfer_summary)

            rune_buy_outcome = ExecutionPhaseOutcome(label="Rune trader buys", measure_label="items")
            rune_buys_started_at = time.perf_counter()
            if storage_transfer_ready and rune_trader_coords and plan.rune_trader_buys:
                rune_buy_outcome = yield from self._buy_planned_rune_trader_items(
                    rune_trader_coords,
                    plan.rune_trader_buys,
                    phase_label="Rune trader buys",
                )
            self.last_execution_phase_durations_ms["rune_buys"] = max(0.0, (time.perf_counter() - rune_buys_started_at) * 1000.0)
            rune_buy_summary = self._format_execution_phase_summary(rune_buy_outcome)
            if rune_buy_summary:
                phase_summaries.append(rune_buy_summary)

            merchant_buy_outcome = ExecutionPhaseOutcome(
                label="Merchant stock",
                measure_label="targets queued",
                attempted=len(plan.merchant_stock_buys),
            )
            merchant_buy_started_at = time.perf_counter()
            if merchant_coords and plan.merchant_stock_buys:
                self._debug_log(
                    f"Merchant buy phase: coords={self._format_debug_coords(merchant_coords)} "
                    f"stock_targets={len(plan.merchant_stock_buys)}"
                )
                merchant_items = yield from self._open_merchant(merchant_coords)
                if merchant_items:
                    for merchant_buy in plan.merchant_stock_buys:
                        bought = yield from self._buy_merchant_model(merchant_buy.model_id, merchant_buy.quantity)
                        if not bought:
                            merchant_buy_outcome.unavailable += 1
                            ConsoleLog(
                                MODULE_NAME,
                                f"Merchant stock target {merchant_buy.model_id} was not offered by the merchant.",
                                Console.MessageType.Warning,
                            )
                        else:
                            merchant_buy_outcome.completed += 1
                else:
                    merchant_buy_outcome.load_failures += 1
                    ConsoleLog(MODULE_NAME, "Merchant inventory did not load for merchant-buy actions.", Console.MessageType.Warning)
                    self._debug_log("Merchant buy phase: inventory did not load.")
            self.last_execution_phase_durations_ms["merchant_stock"] = max(0.0, (time.perf_counter() - merchant_buy_started_at) * 1000.0)
            merchant_buy_summary = self._format_execution_phase_summary(merchant_buy_outcome)
            if merchant_buy_summary:
                phase_summaries.append(merchant_buy_summary)

            common_material_buys = [buy for buy in plan.material_buys if buy.merchant_type == MERCHANT_TYPE_MATERIALS]
            common_buy_outcome = ExecutionPhaseOutcome(label="Material buys", measure_label="trades")
            common_buys_started_at = time.perf_counter()
            if material_coords and common_material_buys:
                self._debug_log(
                    f"Material trader buy phase: coords={self._format_debug_coords(material_coords)} "
                    f"buy_targets={len(common_material_buys)}"
                )
                common_buy_outcome = yield from self._buy_planned_materials(
                    material_coords,
                    common_material_buys,
                    phase_label="Material buys",
                )
            self.last_execution_phase_durations_ms["material_buys"] = max(0.0, (time.perf_counter() - common_buys_started_at) * 1000.0)
            common_buy_summary = self._format_execution_phase_summary(common_buy_outcome)
            if common_buy_summary:
                phase_summaries.append(common_buy_summary)

            rare_coords = plan.coords.get(MERCHANT_TYPE_RARE_MATERIALS)
            rare_material_buys = [buy for buy in plan.material_buys if buy.merchant_type == MERCHANT_TYPE_RARE_MATERIALS]
            rare_buy_outcome = ExecutionPhaseOutcome(label="Rare material buys", measure_label="trades")
            rare_buys_started_at = time.perf_counter()
            if rare_coords and rare_material_buys:
                self._debug_log(
                    f"Rare material trader buy phase: coords={self._format_debug_coords(rare_coords)} "
                    f"buy_targets={len(rare_material_buys)}"
                )
                rare_buy_outcome = yield from self._buy_planned_materials(
                    rare_coords,
                    rare_material_buys,
                    phase_label="Rare material buys",
                )
            self.last_execution_phase_durations_ms["rare_material_buys"] = max(0.0, (time.perf_counter() - rare_buys_started_at) * 1000.0)
            rare_buy_summary = self._format_execution_phase_summary(rare_buy_outcome)
            if rare_buy_summary:
                phase_summaries.append(rare_buy_summary)

            cleanup_outcome = ExecutionPhaseOutcome(label="Cleanup / Xunlai", measure_label="items")
            cleanup_started_at = time.perf_counter()
            if plan.cleanup_transfers:
                storage_ready = self._is_storage_open()
                if not storage_ready and local_only and not storage_available_here:
                    cleanup_outcome.load_failures += 1
                    phase_summaries.append("Planned Xunlai cleanup was skipped because Xunlai is not available here.")
                elif not storage_ready:
                    storage_ready = yield from self._ensure_storage_open(purpose="planned Xunlai cleanup")
                if storage_ready:
                    cleanup_outcome = yield from self._execute_storage_transfers(
                        plan.cleanup_transfers,
                        phase_label="Storage deposits",
                    )
                else:
                    cleanup_outcome.load_failures += 1
                    ConsoleLog(
                        MODULE_NAME,
                        "Could not open Xunlai for planned cleanup transfers.",
                        Console.MessageType.Warning,
                    )
                    phase_summaries.append("Planned Xunlai cleanup was skipped because Xunlai could not be opened.")
            self.last_execution_phase_durations_ms["cleanup_deposits"] = max(0.0, (time.perf_counter() - cleanup_started_at) * 1000.0)
            cleanup_summary = self._format_execution_phase_summary(cleanup_outcome)
            if cleanup_summary:
                self.last_cleanup_summary = cleanup_summary
                phase_summaries.append(cleanup_summary)

            if local_only:
                phase_summaries.insert(
                    0,
                    f"Execute Here: {actionable_here_count} local action(s) | {skipped_here_count} skipped / unavailable.",
                )
            self.last_execution_summary = " ".join(summary for summary in phase_summaries if summary).strip()
            if not self.last_execution_summary:
                self.last_execution_summary = "Execution finished, but no merchant actions reported a completed or attempted outcome."
            self.status_message = (
                "Execute Here finished. Preview again to refresh the post-run state."
                if local_only
                else "Travel + Execute finished. Preview again to refresh the post-run state."
            )
            self.preview_ready = False
            self._debug_log(self.last_execution_summary)
        except Exception as exc:
            self.last_error = f"{exc}"
            self.status_message = "Execution failed. See the console log for details."
            ConsoleLog(MODULE_NAME, f"Execution error: {exc}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, traceback.format_exc(), Console.MessageType.Error)
        finally:
            self.execution_running = False
            if paused_inventory_plus is not None:
                paused_inventory_plus.resume()
                self._debug_log("Execution: resumed Inventory Plus.")
            yield

    def _execute_cleanup_now(self, *, auto_triggered: bool = False):
        self.auto_cleanup_running = True
        self.last_error = ""
        self.last_cleanup_summary = ""
        paused_inventory_plus = None
        try:
            self._invalidate_supported_context_cache()
            plan = self._build_plan(cleanup_only=True)
            if not plan.cleanup_transfers:
                self.last_cleanup_summary = (
                    "Auto cleanup found nothing to move."
                    if auto_triggered
                    else "Cleanup / Xunlai found nothing to move."
                )
                self.status_message = self.last_cleanup_summary
                return

            paused_inventory_plus = self._pause_inventory_plus()
            if paused_inventory_plus is not None:
                self._debug_log("Cleanup / Xunlai: paused Inventory Plus.")

            storage_ready = self._is_storage_open()
            if not storage_ready:
                self.status_message = "Opening Xunlai for cleanup."
                storage_ready = yield from self._ensure_storage_open(purpose="planned Xunlai cleanup")

            cleanup_outcome = ExecutionPhaseOutcome(label="Cleanup / Xunlai", measure_label="items")
            if storage_ready:
                cleanup_outcome = yield from self._execute_storage_transfers(
                    plan.cleanup_transfers,
                    phase_label="Cleanup / Xunlai",
                )
            else:
                cleanup_outcome.load_failures += 1
                ConsoleLog(
                    MODULE_NAME,
                    "Could not open Xunlai for cleanup transfers.",
                    Console.MessageType.Warning,
                )

            cleanup_summary = self._format_execution_phase_summary(cleanup_outcome)
            if cleanup_summary:
                self.last_cleanup_summary = cleanup_summary
            elif cleanup_outcome.completed > 0:
                self.last_cleanup_summary = f"Cleanup / Xunlai moved {cleanup_outcome.completed} item(s)."
            else:
                self.last_cleanup_summary = (
                    "Auto cleanup found nothing to move."
                    if auto_triggered
                    else "Cleanup / Xunlai found nothing to move."
                )

            if cleanup_outcome.completed > 0:
                self._mark_preview_dirty()
            self.status_message = self.last_cleanup_summary
            self._debug_log(self.last_cleanup_summary)
        except Exception as exc:
            self.last_error = f"{exc}"
            self.last_cleanup_summary = "Cleanup / Xunlai failed. See the console log for details."
            self.status_message = self.last_cleanup_summary
            ConsoleLog(MODULE_NAME, f"Cleanup / Xunlai error: {exc}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, traceback.format_exc(), Console.MessageType.Error)
        finally:
            self.auto_cleanup_running = False
            if paused_inventory_plus is not None:
                paused_inventory_plus.resume()
                self._debug_log("Cleanup / Xunlai: resumed Inventory Plus.")
            yield

    def _update_auto_cleanup_runtime(self):
        if not Map.IsMapReady():
            return
        if not self.auto_cleanup_on_outpost_entry or not self._has_cleanup_sources():
            return
        if not (Map.IsOutpost() or Map.IsGuildHall()):
            return
        if (
            self.execution_running
            or self.travel_preview_running
            or self.instant_destroy_running
            or self.storage_scan_running
            or self.auto_cleanup_running
        ):
            return
        if self.auto_cleanup_zone_attempted:
            return

        self.auto_cleanup_zone_attempted = True
        self._queue_cleanup_now(auto_triggered=True)

    def _get_inventory_signature(self, items: list[InventoryItemInfo] | None = None) -> tuple[tuple[int, int], ...]:
        if items is None:
            return tuple(
                sorted(
                    (
                        int(item_id),
                        max(0, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))),
                    )
                    for item_id in self._get_inventory_item_ids()
                    if int(item_id) > 0
                )
            )
        return tuple(
            sorted(
                (
                    int(item.item_id),
                    max(0, int(item.quantity)),
                )
                for item in items
                if int(item.item_id) > 0
            )
        )

    def _request_instant_destroy_rescan(self):
        self.instant_destroy_rescan_requested = True

    def _run_instant_destroy_pass(self):
        if self.instant_destroy_running or not self.destroy_instant_enabled:
            return

        self.instant_destroy_running = True
        paused_inventory_plus = None
        try:
            enabled_destroy_rules = self._collect_enabled_destroy_rules()
            items = self._collect_inventory_items()
            self.instant_destroy_last_signature = self._get_inventory_signature(items)
            if not enabled_destroy_rules:
                self.last_instant_destroy_summary = "Instant Destroy is enabled, but no destroy rules are active."
                return

            instant_plan = PlanResult(supported_map=True, coords={MERCHANT_TYPE_INVENTORY: None})
            self._plan_destroy_actions(
                instant_plan,
                items,
                enabled_destroy_rules,
                self._collect_enabled_sell_rules(),
                set(),
            )
            protected_skip_count = sum(
                1
                for entry in instant_plan.entries
                if entry.action_type == "destroy"
                and entry.merchant_type == MERCHANT_TYPE_INVENTORY
                and entry.state == PLAN_STATE_SKIPPED
                and int(entry.quantity) > 0
                and str(entry.reason).startswith("Blocked by ")
            )
            blocked_destroy_count = sum(
                1
                for entry in instant_plan.entries
                if entry.action_type == "destroy"
                and entry.merchant_type == MERCHANT_TYPE_INVENTORY
                and entry.state == PLAN_STATE_SKIPPED
                and str(entry.reason).startswith("Blocked by ")
            )
            destroy_actions = list({
                int(action.item_id): action
                for action in instant_plan.destroy_actions
                if int(action.item_id) > 0
            }.values())
            if not destroy_actions and instant_plan.destroy_item_ids:
                destroy_actions = [
                    int(item_id)
                    for item_id in dict.fromkeys(instant_plan.destroy_item_ids)
                    if int(item_id) > 0
                ]
            if not destroy_actions:
                if protected_skip_count > 0:
                    self.last_instant_destroy_summary = f"Instant Destroy skipped {protected_skip_count} protected item(s)."
                elif blocked_destroy_count > 0:
                    self.last_instant_destroy_summary = (
                        "Instant Destroy found matching items, but a required stack split could not be performed safely."
                    )
                else:
                    self.last_instant_destroy_summary = "Instant Destroy found no matching items."
                return

            paused_inventory_plus = self._pause_inventory_plus()
            destroy_outcome = yield from self._execute_destroy_phase(destroy_actions)
            if destroy_outcome.completed > 0:
                self._mark_preview_dirty("Inventory changed due to Instant Destroy. Preview again before execution.")

            summary_parts: list[str] = []
            if destroy_outcome.completed > 0:
                summary_parts.append(f"Instant Destroy removed {destroy_outcome.completed} item(s).")
            else:
                summary_parts.append("Instant Destroy found matching items, but none were confirmed destroyed.")
            if protected_skip_count > 0:
                summary_parts.append(f"Skipped {protected_skip_count} protected item(s).")
            if destroy_outcome.timeout_failures > 0:
                summary_parts.append(f"{destroy_outcome.timeout_failures} destroy confirmation timeout(s).")
            if destroy_outcome.depleted > 0:
                summary_parts.append(f"{destroy_outcome.depleted} item(s) were already gone.")
            self.last_instant_destroy_summary = " ".join(summary_parts)
        finally:
            if paused_inventory_plus is not None:
                paused_inventory_plus.resume()
            self.instant_destroy_running = False
            self.instant_destroy_rescan_requested = False
            self.instant_destroy_poll_timer.Reset()
            self.instant_destroy_last_signature = self._get_inventory_signature()
            yield

    def _update_instant_destroy_runtime(self):
        if not Map.IsMapReady():
            return
        if self.execution_running or self.travel_preview_running or self.instant_destroy_running or self.auto_cleanup_running:
            return

        current_signature = self._get_inventory_signature()
        if not self.destroy_instant_enabled:
            self.instant_destroy_rescan_requested = False
            self.instant_destroy_last_signature = current_signature
            return

        should_rescan = bool(self.instant_destroy_rescan_requested)
        if not should_rescan:
            if current_signature == self.instant_destroy_last_signature:
                return
            if not self.instant_destroy_poll_timer.IsExpired():
                return

        self.instant_destroy_rescan_requested = False
        self.instant_destroy_poll_timer.Reset()
        GLOBAL_CACHE.Coroutines.append(self._run_instant_destroy_pass())

    def _push_active_button_style(self, color: tuple[float, float, float, float]):
        base = (max(color[0] - 0.06, 0.0), max(color[1] - 0.10, 0.0), max(color[2] - 0.06, 0.0), 0.46)
        hover = (max(color[0] - 0.03, 0.0), max(color[1] - 0.06, 0.0), max(color[2] - 0.03, 0.0), 0.58)
        active = (max(color[0] - 0.08, 0.0), max(color[1] - 0.12, 0.0), max(color[2] - 0.08, 0.0), 0.68)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, base)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active)

    def _push_rule_header_hover_style(self):
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0.15, 0.16, 0.19, 0.08))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0.24, 0.25, 0.29, 0.34))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0.20, 0.21, 0.25, 0.46))

    def _draw_workspace_button(self, label: str, *, active: bool, color: tuple[float, float, float, float]) -> bool:
        if active:
            self._push_active_button_style(color)
        clicked = PyImGui.button(label)
        if active:
            PyImGui.pop_style_color(3)
        return bool(clicked)

    def _draw_inline_badge(self, label: str, color: tuple[float, float, float, float]):
        PyImGui.text_colored(f"[{label}]", color)

    def _draw_section_heading(self, label: str):
        PyImGui.text_colored(label, UI_COLOR_SECTION_HEADING)

    def _draw_secondary_text(self, text: str, *, wrapped: bool = True):
        if not text:
            return
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI_COLOR_SECONDARY_TEXT)
        if wrapped:
            PyImGui.text_wrapped(text)
        else:
            PyImGui.text(text)
        PyImGui.pop_style_color(1)

    def _draw_rule_kind_tabs(
        self,
        *,
        workspace_id: str,
        active_kind: str,
        kind_order: tuple[str, ...],
        tab_labels: dict[str, str],
        rule_counts: dict[str, int],
    ) -> str:
        if not kind_order:
            return active_kind

        next_active_kind = active_kind if active_kind in kind_order else kind_order[0]
        for tab_index, kind in enumerate(kind_order):
            tab_label = str(tab_labels.get(kind, kind)).strip() or str(kind)
            _, tab_color = self._get_rule_type_presentation(kind)
            button_label = f"{tab_label} ({max(0, int(rule_counts.get(kind, 0)))})##{workspace_id}_{kind}"
            if self._draw_workspace_button(button_label, active=next_active_kind == kind, color=tab_color):
                next_active_kind = kind
            if tab_index + 1 < len(kind_order):
                PyImGui.same_line(0, 6)
        return next_active_kind

    def _is_actionable_preview_entry(self, entry: ExecutionPlanEntry) -> bool:
        return str(entry.state) in (PLAN_STATE_WILL_EXECUTE, PLAN_STATE_CONDITIONAL)

    def _split_preview_entries(self, entries: list[ExecutionPlanEntry]) -> tuple[list[ExecutionPlanEntry], list[ExecutionPlanEntry]]:
        actionable = [entry for entry in entries if self._is_actionable_preview_entry(entry)]
        skipped = [entry for entry in entries if not self._is_actionable_preview_entry(entry)]
        return actionable, skipped

    def _get_preview_here_availability(self) -> dict[str, bool]:
        try:
            supported_map, _reason, coords = self._get_supported_context(passive=True)
        except TypeError:
            supported_map, _reason, coords = self._get_supported_context()
        availability_here = {
            MERCHANT_TYPE_MERCHANT: bool(coords.get(MERCHANT_TYPE_MERCHANT)),
            MERCHANT_TYPE_MATERIALS: bool(coords.get(MERCHANT_TYPE_MATERIALS)),
            MERCHANT_TYPE_RUNE_TRADER: bool(coords.get(MERCHANT_TYPE_RUNE_TRADER)),
            MERCHANT_TYPE_RARE_MATERIALS: bool(coords.get(MERCHANT_TYPE_RARE_MATERIALS)),
            MERCHANT_TYPE_STORAGE: self._has_local_storage_access(),
            MERCHANT_TYPE_INVENTORY: True,
            MERCHANT_TYPE_TRAVEL: False,
        }
        if not supported_map:
            availability_here[MERCHANT_TYPE_MERCHANT] = False
            availability_here[MERCHANT_TYPE_MATERIALS] = False
            availability_here[MERCHANT_TYPE_RUNE_TRADER] = False
            availability_here[MERCHANT_TYPE_RARE_MATERIALS] = False
        return availability_here

    def _preview_entry_needs_local_storage_access(
        self,
        entry: ExecutionPlanEntry,
        *,
        plan: PlanResult | None = None,
    ) -> bool:
        safe_plan = plan if plan is not None else self.preview_plan
        merchant_type = str(entry.merchant_type)
        action_type = str(entry.action_type)
        if merchant_type == MERCHANT_TYPE_STORAGE:
            return True
        if merchant_type == MERCHANT_TYPE_RUNE_TRADER and action_type == "buy":
            return self._plan_needs_exact_storage_scan(safe_plan)
        return False

    def _is_preview_entry_available_here(
        self,
        entry: ExecutionPlanEntry,
        *,
        availability_here: dict[str, bool] | None = None,
        plan: PlanResult | None = None,
    ) -> bool:
        safe_plan = plan if plan is not None else self.preview_plan
        local_availability = availability_here if availability_here is not None else self._get_preview_here_availability()
        merchant_type = str(entry.merchant_type)
        action_type = str(entry.action_type)
        if merchant_type == MERCHANT_TYPE_TRAVEL or action_type == "travel":
            return False
        if merchant_type == MERCHANT_TYPE_INVENTORY:
            base_available = True
        else:
            base_available = bool(local_availability.get(merchant_type, False))
        if not base_available:
            return False
        if self._preview_entry_needs_local_storage_access(entry, plan=safe_plan):
            return bool(local_availability.get(MERCHANT_TYPE_STORAGE, False))
        return True

    def _get_preview_unavailable_here_reason(
        self,
        entry: ExecutionPlanEntry,
        *,
        availability_here: dict[str, bool] | None = None,
        plan: PlanResult | None = None,
    ) -> str:
        safe_plan = plan if plan is not None else self.preview_plan
        local_availability = availability_here if availability_here is not None else self._get_preview_here_availability()
        merchant_type = str(entry.merchant_type)
        action_type = str(entry.action_type)
        if merchant_type == MERCHANT_TYPE_TRAVEL or action_type == "travel":
            return ""
        if self._is_preview_entry_available_here(
            entry,
            availability_here=local_availability,
            plan=safe_plan,
        ):
            return ""
        if merchant_type != MERCHANT_TYPE_INVENTORY and not bool(local_availability.get(merchant_type, False)):
            merchant_label = MERCHANT_TYPE_LABELS.get(merchant_type, merchant_type)
            return f"{merchant_label} not available here."
        if self._preview_entry_needs_local_storage_access(entry, plan=safe_plan):
            return f"{MERCHANT_TYPE_LABELS[MERCHANT_TYPE_STORAGE]} not available here."
        return "Not available here."

    def _get_locally_actionable_preview_counts(
        self,
        plan: PlanResult,
        *,
        availability_here: dict[str, bool] | None = None,
    ) -> tuple[int, int]:
        local_availability = availability_here if availability_here is not None else self._get_preview_here_availability()
        actionable_entries, skipped_entries = self._split_preview_entries(plan.entries)
        actionable_here_count = sum(
            1
            for entry in actionable_entries
            if self._is_preview_entry_available_here(
                entry,
                availability_here=local_availability,
                plan=plan,
            )
        )
        skipped_here_count = len(skipped_entries) + max(0, len(actionable_entries) - actionable_here_count)
        return actionable_here_count, skipped_here_count

    def _get_preview_entry_counts(self, entries: list[ExecutionPlanEntry]) -> tuple[int, int, int]:
        direct_count = sum(1 for entry in entries if str(entry.state) == PLAN_STATE_WILL_EXECUTE)
        conditional_count = sum(1 for entry in entries if str(entry.state) == PLAN_STATE_CONDITIONAL)
        skipped_count = len(entries) - direct_count - conditional_count
        return direct_count, conditional_count, max(0, skipped_count)

    def _plan_has_local_destroy_actions(self, plan: PlanResult) -> bool:
        return bool(plan.destroy_actions or plan.destroy_item_ids)

    def _plan_has_local_storage_actions(self, plan: PlanResult) -> bool:
        return bool(
            plan.cleanup_transfers
            or any(str(transfer.direction) == STORAGE_TRANSFER_DEPOSIT for transfer in plan.storage_transfers)
        )

    def _plan_has_conditional_storage_actions(self, plan: PlanResult) -> bool:
        return any(
            str(entry.action_type) in {"deposit", "withdraw"}
            and str(entry.state) == PLAN_STATE_CONDITIONAL
            for entry in plan.entries
        )

    def _plan_has_direct_storage_actions(self, plan: PlanResult) -> bool:
        return any(
            str(entry.action_type) in {"deposit", "withdraw"}
            and str(entry.state) == PLAN_STATE_WILL_EXECUTE
            for entry in plan.entries
        )

    def _plan_has_conditional_cleanup_actions(self, plan: PlanResult) -> bool:
        return any(
            str(entry.action_type) == "deposit"
            and str(entry.merchant_type) == MERCHANT_TYPE_STORAGE
            and str(entry.state) == PLAN_STATE_CONDITIONAL
            for entry in plan.entries
        )

    def _plan_has_direct_cleanup_actions(self, plan: PlanResult) -> bool:
        return any(
            str(entry.action_type) == "deposit"
            and str(entry.merchant_type) == MERCHANT_TYPE_STORAGE
            and str(entry.state) == PLAN_STATE_WILL_EXECUTE
            for entry in plan.entries
        )

    def _plan_needs_exact_storage_scan(self, plan: PlanResult) -> bool:
        if str(plan.storage_plan_state) != STORAGE_PLAN_STATE_NEEDS_EXACT_SCAN:
            return False
        return any(
            str(entry.merchant_type) == MERCHANT_TYPE_RUNE_TRADER
            and str(entry.state) == PLAN_STATE_CONDITIONAL
            for entry in plan.entries
        )

    def _can_run_preview_exact_storage_scan(self) -> bool:
        return bool(
            self.preview_ready
            and self._can_use_local_storage_actions()
            and self._plan_needs_exact_storage_scan(self.preview_plan)
        )

    def _format_compact_list(self, labels: list[str], limit: int = 2) -> str:
        cleaned = [str(label).strip() for label in labels if str(label).strip()]
        if not cleaned:
            return ""
        if len(cleaned) <= limit:
            return ", ".join(cleaned)
        return f"{', '.join(cleaned[:limit])} +{len(cleaned) - limit} more"

    def _get_display_sort_text(self, value: object) -> str:
        return str(value or "").strip().casefold()

    def _get_model_display_sort_key(self, model_id: object) -> tuple[str, int]:
        safe_model_id = max(0, _safe_int(model_id, 0))
        return (self._get_display_sort_text(self._format_model_label(safe_model_id)), safe_model_id)

    def _get_identifier_display_sort_key(self, identifier: object, formatter) -> tuple[str, str]:
        safe_identifier = str(identifier or "").strip()
        return (self._get_display_sort_text(formatter(safe_identifier)), safe_identifier.casefold())

    def _sort_model_ids_for_display(self, model_ids: list[int]) -> list[int]:
        return sorted(list(model_ids), key=self._get_model_display_sort_key)

    def _sort_targets_by_model_label_for_display(self, targets: list[object]) -> list[object]:
        return sorted(
            list(targets),
            key=lambda target: self._get_model_display_sort_key(getattr(target, "model_id", 0)),
        )

    def _sort_identifiers_for_display(self, identifiers: list[str], formatter) -> list[str]:
        return sorted(
            list(identifiers),
            key=lambda identifier: self._get_identifier_display_sort_key(identifier, formatter),
        )

    def _sort_targets_by_identifier_label_for_display(self, targets: list[object], formatter) -> list[object]:
        return sorted(
            list(targets),
            key=lambda target: self._get_identifier_display_sort_key(getattr(target, "identifier", ""), formatter),
        )

    def _format_rule_index_list(self, indices: list[int], limit: int = 3, rules: list[object] | None = None) -> str:
        labels: list[str] = []
        for index in indices:
            label = f"#{int(index) + 1}"
            if rules is not None and 0 <= int(index) < len(rules):
                custom_name = self._get_rule_custom_name(rules[int(index)])
                if custom_name:
                    label = f"{label} {custom_name}"
            labels.append(label)
        return self._format_compact_list(labels, limit=limit)

    def _get_support_state(self, supported_map: bool, coords: dict[str, tuple[float, float] | None]) -> tuple[str, tuple[float, float, float, float]]:
        resolved_count = sum(1 for value in coords.values() if value is not None)
        if not supported_map:
            return "Unavailable", UI_COLOR_DANGER
        if resolved_count < len(coords):
            return "Partial", UI_COLOR_WARNING
        return "Ready", UI_COLOR_SUCCESS

    def _get_preview_state(self) -> tuple[str, tuple[float, float, float, float], str]:
        actionable, skipped = self._split_preview_entries(self.preview_plan.entries)
        if self.execution_running or self.travel_preview_running or self.instant_destroy_running or self.storage_scan_running or self.auto_cleanup_running:
            return "Busy", UI_COLOR_WARNING, "Preview, cleanup, storage scan, or execution is currently running."
        if self.preview_ready:
            if self._preview_has_execute_travel_pending():
                target_label = self.preview_execute_travel_target_outpost_name or "the selected outpost"
                detail = (
                    f"Preview is projected assuming Auto Travel reaches {target_label}. "
                    "Travel + Execute will travel, rebuild live merchant handling, and then run the plan. "
                    "Execute Here runs only green local entries."
                )
                if actionable:
                    return "Projected", UI_COLOR_INFO, detail
                if skipped:
                    return "Projected", UI_COLOR_MUTED, detail
                return "Projected", UI_COLOR_MUTED, detail
            if actionable:
                return "Ready", UI_COLOR_SUCCESS, f"{len(actionable)} action(s) queued from the current preview."
            if skipped:
                return "Ready", UI_COLOR_MUTED, "Preview is current, but nothing will execute."
            return "Ready", UI_COLOR_MUTED, "Preview is current."
        return "Stale", UI_COLOR_WARNING, "Run Preview to refresh the current map and inventory state."

    def _draw_live_config_recovery_section(self):
        backup_path = self._get_available_profile_backup_path(self.config_path) if self.config_path else ""
        backup_exists = bool(backup_path and os.path.exists(backup_path))
        config_folder = os.path.dirname(self.config_path) if self.config_path else CONFIG_DIR
        recovery_folder = self._get_profile_recovery_dir(self.config_path) if self.config_path else RECOVERY_DIR
        config_label = os.path.basename(self.config_path) if self.config_path else "Not initialized"
        self._draw_secondary_text(
            "These tools recover the current account's live working config and its last automatic backup. "
            "They do not manage shared saved profiles."
        )
        self._draw_secondary_text(f"Live Config: {config_label}", wrapped=False)
        if backup_exists:
            self._draw_secondary_text(f"Last backup: {os.path.basename(backup_path)}", wrapped=False)
        else:
            self._draw_secondary_text("Last backup: none found yet.", wrapped=False)
        self._draw_secondary_text(f"Config Folder: {config_folder}")
        self._draw_secondary_text(f"Recovery Folder: {recovery_folder}")

        PyImGui.begin_disabled(not backup_exists)
        restore_clicked = PyImGui.button("Restore Last Backup##merchant_rules_restore_backup")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        open_folder_clicked = PyImGui.button("Open Config Folder##merchant_rules_open_config_folder")

        if restore_clicked:
            self._restore_profile_from_backup()
        if open_folder_clicked:
            self._open_profile_config_folder()

    def _draw_runtime_diagnostics_section(self):
        total_lookups = max(0, int(self.inventory_modifier_cache_hits) + int(self.inventory_modifier_cache_misses))
        hit_rate = self._get_modifier_cache_hit_rate()
        self._draw_secondary_text(
            f"Modifier cache: {len(self.inventory_modifier_cache)} entry(s) | {self.inventory_modifier_cache_hits} hit(s) | "
            f"{self.inventory_modifier_cache_misses} miss(es) | {hit_rate:.1f}% hit rate",
            wrapped=False,
        )
        self._draw_secondary_text(
            f"Last inventory snapshot: {self.last_inventory_snapshot_duration_ms:.2f} ms | "
            f"Last plan build: {self.last_plan_build_duration_ms:.2f} ms | "
            f"Last compare: {self.last_preview_compare_duration_ms:.2f} ms",
            wrapped=False,
        )
        if total_lookups <= 0:
            self._draw_secondary_text("Modifier cache stats will populate after the next preview or execute run.")
        if self.last_execution_phase_durations_ms:
            ordered_phase_labels = (
                ("destroys", "Destroy"),
                ("merchant_stock", "Merchant stock"),
                ("material_sales", "Material sales"),
                ("rare_material_sales", "Rare material sales"),
                ("merchant_sells", "Merchant sells"),
                ("rune_sales", "Rune sales"),
                ("storage_transfers", "Storage withdraws"),
                ("rune_buys", "Rune buys"),
                ("material_buys", "Material buys"),
                ("rare_material_buys", "Rare buys"),
                ("cleanup_deposits", "Cleanup / Xunlai"),
            )
            phase_rows = [
                f"{label}: {self.last_execution_phase_durations_ms[key]:.2f} ms"
                for key, label in ordered_phase_labels
                if key in self.last_execution_phase_durations_ms
            ]
            if phase_rows:
                self._draw_secondary_text("Last execution timings:", wrapped=False)
                for phase_row in phase_rows:
                    self._draw_secondary_text(phase_row, wrapped=False)

        if PyImGui.small_button("Clear Runtime Stats##merchant_rules_clear_runtime_stats"):
            self._clear_runtime_diagnostics()
            self.status_message = "Merchant Rules runtime diagnostics cleared."
        PyImGui.same_line(0, 8)
        if PyImGui.small_button("Clear Modifier Cache##merchant_rules_clear_modifier_cache"):
            self.inventory_modifier_cache.clear()
            self.status_message = "Merchant Rules modifier cache cleared."

    def _get_enabled_rarity_labels(self, rule: object) -> list[str]:
        return [
            label
            for rarity_key, label in _get_rarity_options_for_rule(str(getattr(rule, "kind", "")))
            if bool(getattr(rule, "rarities", {}).get(rarity_key, False))
        ]

    def _get_rule_type_presentation(self, rule_kind: str) -> tuple[str, tuple[float, float, float, float]]:
        return RULE_KIND_PRESENTATION.get(str(rule_kind), ("Rule", UI_COLOR_SUBTLE))

    def _get_buy_rule_summary(self, rule: BuyRule) -> tuple[str, bool]:
        normalized_rule = _normalize_buy_rule(rule)
        if normalized_rule is None:
            return "Legacy rule removed on load.", False
        if normalized_rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
            rune_targets = _normalize_rune_trader_targets(normalized_rule.rune_targets)
            if not rune_targets:
                return "Choose one or more rune or insignia targets to maintain.", False
            if len(rune_targets) == 1:
                rune_target = rune_targets[0]
                parts = [self._get_rune_label(rune_target.identifier)]
                if rune_target.target_count > 0:
                    parts.append(f"Target {int(rune_target.target_count)}")
                else:
                    parts.append("No target set")
                if rune_target.max_per_run > 0:
                    parts.append(f"Max/run {int(rune_target.max_per_run)}")
                return " | ".join(parts), True

            target_labels = [
                self._get_rune_label(target.identifier)
                for target in self._sort_targets_by_identifier_label_for_display(rune_targets, self._get_rune_label)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(rune_targets)} rune target(s)"
            return f"{len(rune_targets)} target(s) | {summary}", True
        if normalized_rule.kind == BUY_KIND_MERCHANT_STOCK:
            merchant_stock_targets = _normalize_merchant_stock_targets(normalized_rule.merchant_stock_targets)
            if not merchant_stock_targets:
                return "Choose one or more items to maintain.", False
            if len(merchant_stock_targets) == 1:
                merchant_stock_target = merchant_stock_targets[0]
                parts = [self._format_model_label(merchant_stock_target.model_id)]
                if merchant_stock_target.target_count > 0:
                    parts.append(f"Target {int(merchant_stock_target.target_count)}")
                else:
                    parts.append("No target set")
                if merchant_stock_target.max_per_run > 0:
                    parts.append(f"Max/run {int(merchant_stock_target.max_per_run)}")
                return " | ".join(parts), True

            target_labels = [
                self._get_model_name(target.model_id) or str(target.model_id)
                for target in self._sort_targets_by_model_label_for_display(merchant_stock_targets)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(merchant_stock_targets)} stock target(s)"
            return f"{len(merchant_stock_targets)} stock target(s) | {summary}", True

        material_targets = _normalize_material_targets(normalized_rule.material_targets)
        if not material_targets:
            return "Add one or more materials to maintain.", False
        material_labels = [
            self._get_model_name(target.model_id) or str(target.model_id)
            for target in self._sort_targets_by_model_label_for_display(material_targets)
        ]
        summary = self._format_compact_list(material_labels, limit=2) or f"{len(material_targets)} material target(s)"
        return f"{len(material_targets)} material target(s) | {summary}", True

    def _get_sell_rule_summary(self, rule: SellRule) -> tuple[str, bool]:
        normalized_rule = _normalize_sell_rule(rule)
        if normalized_rule is None:
            return "Unsupported legacy sell rule type.", False
        if normalized_rule.kind == SELL_KIND_COMMON_MATERIALS:
            whitelist_targets = _normalize_whitelist_targets(getattr(normalized_rule, "whitelist_targets", []))
            if not whitelist_targets:
                return "Pick the materials to sell.", False
            target_labels = [
                f"{self._get_model_name(target.model_id) or str(target.model_id)} keep {int(target.keep_count)}"
                for target in self._sort_targets_by_model_label_for_display(whitelist_targets)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(whitelist_targets)} material target(s)"
            return f"{len(whitelist_targets)} material target(s) | {summary}", True
        if normalized_rule.kind == SELL_KIND_EXPLICIT_MODELS:
            whitelist_targets = _normalize_whitelist_targets(getattr(normalized_rule, "whitelist_targets", []))
            if not whitelist_targets:
                return "Pick the items to sell.", False
            target_labels = [
                f"{self._get_model_name(target.model_id) or str(target.model_id)} keep {int(target.keep_count)}"
                for target in self._sort_targets_by_model_label_for_display(whitelist_targets)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(whitelist_targets)} selected target(s)"
            return f"{len(whitelist_targets)} selected target(s) | {summary}", True

        enabled_rarities = self._get_enabled_rarity_labels(normalized_rule)
        has_explicit_hard_protection = _has_explicit_equippable_hard_protection(normalized_rule)
        if not enabled_rarities and not has_explicit_hard_protection:
            return "Select at least one rarity tier.", False

        parts = [f"{len(enabled_rarities)} rarity tier(s)"] if enabled_rarities else ["Protection only"]
        if enabled_rarities and normalized_rule.skip_customized:
            parts.append("Skip customized")
        if enabled_rarities and normalized_rule.skip_unidentified:
            parts.append("Skip unidentified")
        if normalized_rule.blacklist_model_ids:
            parts.append(f"Models {len(normalized_rule.blacklist_model_ids)}")
        if normalized_rule.kind == SELL_KIND_WEAPONS and normalized_rule.blacklist_item_type_ids:
            parts.append(f"Weapon types {len(normalized_rule.blacklist_item_type_ids)}")
        if normalized_rule.kind == SELL_KIND_WEAPONS:
            all_weapons_min_requirement, all_weapons_max_requirement = _normalize_weapon_requirement_range(
                getattr(normalized_rule, "all_weapons_min_requirement", 0),
                getattr(normalized_rule, "all_weapons_max_requirement", 0),
            )
            if _is_weapon_requirement_range_active(all_weapons_min_requirement, all_weapons_max_requirement):
                parts.append(f"All weapons req {all_weapons_min_requirement}-{all_weapons_max_requirement}")
            active_requirement_rule_count = sum(
                1
                for requirement_rule in normalized_rule.protected_weapon_requirement_rules
                if _is_weapon_requirement_range_active(
                    getattr(requirement_rule, "min_requirement", 0),
                    getattr(requirement_rule, "max_requirement", 0),
                )
            )
            if active_requirement_rule_count > 0:
                parts.append(f"Req ranges {active_requirement_rule_count}")
        if normalized_rule.kind == SELL_KIND_WEAPONS and normalized_rule.protected_weapon_mod_identifiers:
            parts.append(f"Protected mods {len(normalized_rule.protected_weapon_mod_identifiers)}")
        if normalized_rule.kind == SELL_KIND_ARMOR and normalized_rule.protected_rune_identifiers:
            parts.append(f"Protected runes {len(normalized_rule.protected_rune_identifiers)}")
        if normalized_rule.kind == SELL_KIND_ARMOR and normalized_rule.include_standalone_runes:
            parts.append("Sell standalone runes")
        return " | ".join(parts), True

    def _get_destroy_rule_summary(self, rule: DestroyRule) -> tuple[str, bool]:
        normalized_rule = _normalize_destroy_rule(rule)
        if normalized_rule.kind == DESTROY_KIND_MATERIALS:
            whitelist_targets = _normalize_whitelist_targets(getattr(normalized_rule, "whitelist_targets", []))
            if not whitelist_targets:
                return "Pick the materials to destroy.", False
            target_labels = [
                f"{self._get_model_name(target.model_id) or str(target.model_id)} keep {int(target.keep_count)}"
                for target in self._sort_targets_by_model_label_for_display(whitelist_targets)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(whitelist_targets)} material target(s)"
            return f"{len(whitelist_targets)} material target(s) | {summary}", True
        if normalized_rule.kind == DESTROY_KIND_EXPLICIT_MODELS:
            whitelist_targets = _normalize_whitelist_targets(getattr(normalized_rule, "whitelist_targets", []))
            if not whitelist_targets:
                return "Pick the items to destroy.", False
            target_labels = [
                f"{self._get_model_name(target.model_id) or str(target.model_id)} keep {int(target.keep_count)}"
                for target in self._sort_targets_by_model_label_for_display(whitelist_targets)
            ]
            summary = self._format_compact_list(target_labels, limit=2) or f"{len(whitelist_targets)} selected target(s)"
            return f"{len(whitelist_targets)} selected target(s) | {summary}", True

        enabled_rarities = self._get_enabled_rarity_labels(normalized_rule)
        if not enabled_rarities:
            return "Select at least one rarity tier.", False
        return f"{len(enabled_rarities)} rarity tier(s)", True

    def _get_rule_state_badge(self, *, enabled: bool, ready: bool) -> tuple[str, tuple[float, float, float, float]]:
        if not enabled:
            return "Disabled", UI_COLOR_MUTED
        if ready:
            return "Ready", UI_COLOR_SUCCESS
        return "Needs Setup", UI_COLOR_WARNING

    def _get_buy_rule_overlap_diagnostics(self) -> list[str]:
        diagnostics: list[str] = []
        merchant_stock_rules: dict[int, list[int]] = {}
        material_target_rules: dict[int, list[int]] = {}
        rune_target_rules: dict[str, list[int]] = {}
        for index, raw_rule in enumerate(self.buy_rules):
            rule = _normalize_buy_rule(raw_rule)
            if rule is None or not rule.enabled:
                continue
            if rule.kind == BUY_KIND_MERCHANT_STOCK:
                for target in _normalize_merchant_stock_targets(rule.merchant_stock_targets):
                    if int(target.model_id) > 0:
                        merchant_stock_rules.setdefault(int(target.model_id), []).append(index)
            elif rule.kind == BUY_KIND_MATERIAL_TARGET:
                for target in _normalize_material_targets(rule.material_targets):
                    if int(target.model_id) > 0:
                        material_target_rules.setdefault(int(target.model_id), []).append(index)
            elif rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
                for target in _normalize_rune_trader_targets(rule.rune_targets):
                    if target.identifier:
                        rune_target_rules.setdefault(str(target.identifier), []).append(index)

        for model_id, indices in sorted(merchant_stock_rules.items()):
            if len(indices) < 2:
                continue
            diagnostics.append(
                f"{self._format_model_label(model_id)} is maintained by buy rules {self._format_rule_index_list(indices, rules=self.buy_rules)}. "
                f"Later rules only see leftovers after earlier ones update the simulated stock count."
            )
        for model_id, indices in sorted(material_target_rules.items()):
            if len(indices) < 2:
                continue
            diagnostics.append(
                f"{self._format_model_label(model_id)} appears in buy rules {self._format_rule_index_list(indices, rules=self.buy_rules)}. "
                f"Those rules stack on the same material target."
            )
        for identifier, indices in sorted(rune_target_rules.items(), key=lambda row: self._get_rune_label(row[0]).lower()):
            if len(indices) < 2:
                continue
            diagnostics.append(
                f"{self._get_rune_label(identifier)} is maintained by buy rules {self._format_rule_index_list(indices, rules=self.buy_rules)}. "
                f"Later rules only see shortages left after earlier rune targets update the simulated stock."
            )
        return diagnostics

    def _get_sell_rule_overlap_diagnostics(self) -> list[str]:
        diagnostics: list[str] = []
        explicit_model_rules: dict[int, list[int]] = {}
        material_rules: dict[int, list[int]] = {}
        weapon_rules: list[tuple[int, set[str]]] = []
        armor_rules: list[tuple[int, set[str]]] = []

        for index, raw_rule in enumerate(self.sell_rules):
            rule = _normalize_sell_rule(raw_rule)
            if rule is None:
                continue
            if not rule.enabled:
                continue
            if rule.kind == SELL_KIND_EXPLICIT_MODELS:
                for model_id in rule.model_ids:
                    explicit_model_rules.setdefault(int(model_id), []).append(index)
            elif rule.kind == SELL_KIND_COMMON_MATERIALS:
                for model_id in rule.model_ids:
                    material_rules.setdefault(int(model_id), []).append(index)
            elif rule.kind == SELL_KIND_WEAPONS:
                weapon_rules.append((index, set(self._get_enabled_rarity_labels(rule))))
            elif rule.kind == SELL_KIND_ARMOR:
                armor_rules.append((index, set(self._get_enabled_rarity_labels(rule))))

        for model_id, indices in sorted(explicit_model_rules.items()):
            if len(indices) < 2:
                continue
            diagnostics.append(
                f"{self._format_model_label(model_id)} is listed in sell rules {self._format_rule_index_list(indices, rules=self.sell_rules)}. "
                f"Earlier explicit-model rules allocate matching items first."
            )
        for model_id, indices in sorted(material_rules.items()):
            if len(indices) < 2:
                continue
            diagnostics.append(
                f"{self._format_model_label(model_id)} appears in material sell rules {self._format_rule_index_list(indices, rules=self.sell_rules)}. "
                f"Earlier material rules consume tradable batches first."
            )

        def _append_equippable_overlap_messages(rule_kind_label: str, rule_infos: list[tuple[int, set[str]]]):
            for info_index, (left_index, left_rarities) in enumerate(rule_infos):
                for right_index, right_rarities in rule_infos[info_index + 1:]:
                    overlap = sorted(left_rarities & right_rarities)
                    if not overlap:
                        continue
                    diagnostics.append(
                        f"{rule_kind_label} rules {self._format_rule_index_list([left_index, right_index], limit=2, rules=self.sell_rules)} both include "
                        f"{self._format_compact_list(overlap, limit=3)}. Earlier rules allocate matching items first."
                    )

        _append_equippable_overlap_messages("Weapon", weapon_rules)
        _append_equippable_overlap_messages("Armor", armor_rules)
        return diagnostics

    def _get_destroy_rule_overlap_diagnostics(self) -> list[str]:
        diagnostics: list[str] = []
        destroy_explicit_rules: dict[int, list[int]] = {}
        destroy_material_rules: dict[int, list[int]] = {}
        destroy_weapon_rules: list[tuple[int, set[str]]] = []
        destroy_armor_rules: list[tuple[int, set[str]]] = []

        for index, raw_rule in enumerate(self.destroy_rules):
            rule = _normalize_destroy_rule(raw_rule)
            if not rule.enabled:
                continue
            if rule.kind == DESTROY_KIND_EXPLICIT_MODELS:
                for model_id in rule.model_ids:
                    destroy_explicit_rules.setdefault(int(model_id), []).append(index)
            elif rule.kind == DESTROY_KIND_MATERIALS:
                for model_id in rule.model_ids:
                    destroy_material_rules.setdefault(int(model_id), []).append(index)
            elif rule.kind == DESTROY_KIND_WEAPONS:
                destroy_weapon_rules.append((index, set(self._get_enabled_rarity_labels(rule))))
            elif rule.kind == DESTROY_KIND_ARMOR:
                destroy_armor_rules.append((index, set(self._get_enabled_rarity_labels(rule))))

        for model_id, indices in sorted(destroy_explicit_rules.items()):
            if len(indices) > 1:
                diagnostics.append(
                    f"{self._format_model_label(model_id)} is listed in destroy rules {self._format_rule_index_list(indices, rules=self.destroy_rules)}. Earlier destroy rules claim matching items first."
                )
        for model_id, indices in sorted(destroy_material_rules.items()):
            if len(indices) > 1:
                diagnostics.append(
                    f"{self._format_model_label(model_id)} appears in material destroy rules {self._format_rule_index_list(indices, rules=self.destroy_rules)}. Earlier destroy rules claim matching stacks first."
                )

        for destroy_index, destroy_rarities in destroy_weapon_rules:
            for sell_index, sell_rule in enumerate(self.sell_rules):
                normalized_sell_rule = _normalize_sell_rule(sell_rule)
                if normalized_sell_rule is None or not normalized_sell_rule.enabled or normalized_sell_rule.kind != SELL_KIND_WEAPONS:
                    continue
                overlap = sorted(destroy_rarities & set(self._get_enabled_rarity_labels(normalized_sell_rule)))
                if overlap:
                    diagnostics.append(
                        f"Destroy rule {self._format_rule_index_list([destroy_index], limit=1, rules=self.destroy_rules)} overlaps weapon sell rule {self._format_rule_index_list([sell_index], limit=1, rules=self.sell_rules)} on {self._format_compact_list(overlap, limit=3)}. Destroy claims matching items first."
                    )
        for destroy_index, destroy_rarities in destroy_armor_rules:
            for sell_index, sell_rule in enumerate(self.sell_rules):
                normalized_sell_rule = _normalize_sell_rule(sell_rule)
                if normalized_sell_rule is None or not normalized_sell_rule.enabled or normalized_sell_rule.kind != SELL_KIND_ARMOR:
                    continue
                overlap = sorted(destroy_rarities & set(self._get_enabled_rarity_labels(normalized_sell_rule)))
                if overlap:
                    diagnostics.append(
                        f"Destroy rule {self._format_rule_index_list([destroy_index], limit=1, rules=self.destroy_rules)} overlaps armor sell rule {self._format_rule_index_list([sell_index], limit=1, rules=self.sell_rules)} on {self._format_compact_list(overlap, limit=3)}. Destroy claims matching items first."
                    )

        for destroy_index, raw_rule in enumerate(self.destroy_rules):
            destroy_rule = _normalize_destroy_rule(raw_rule)
            if not destroy_rule.enabled:
                continue
            if destroy_rule.kind not in (DESTROY_KIND_EXPLICIT_MODELS, DESTROY_KIND_MATERIALS):
                continue
            destroy_model_ids = set(int(model_id) for model_id in destroy_rule.model_ids)
            if not destroy_model_ids:
                continue

            for sell_index, raw_sell_rule in enumerate(self.sell_rules):
                sell_rule = _normalize_sell_rule(raw_sell_rule)
                if sell_rule is None or not sell_rule.enabled:
                    continue
                if sell_rule.kind not in (SELL_KIND_EXPLICIT_MODELS, SELL_KIND_COMMON_MATERIALS):
                    continue
                overlap_ids = sorted(destroy_model_ids & set(int(model_id) for model_id in sell_rule.model_ids))
                if overlap_ids:
                    diagnostics.append(
                        f"Destroy rule {self._format_rule_index_list([destroy_index], limit=1, rules=self.destroy_rules)} overlaps sell rule {self._format_rule_index_list([sell_index], limit=1, rules=self.sell_rules)} on {self._format_compact_list([self._format_model_label(model_id) for model_id in overlap_ids], limit=2)}. Destroy claims matching items first."
                    )

            for buy_index, raw_buy_rule in enumerate(self.buy_rules):
                buy_rule = _normalize_buy_rule(raw_buy_rule)
                if buy_rule is None or not buy_rule.enabled:
                    continue
                buy_model_ids: set[int] = set()
                if buy_rule.kind == BUY_KIND_MATERIAL_TARGET:
                    buy_model_ids = {int(target.model_id) for target in buy_rule.material_targets}
                elif buy_rule.kind == BUY_KIND_MERCHANT_STOCK:
                    buy_model_ids = {int(target.model_id) for target in buy_rule.merchant_stock_targets}
                overlap_ids = sorted(destroy_model_ids & buy_model_ids)
                if overlap_ids:
                    diagnostics.append(
                        f"Destroy rule {self._format_rule_index_list([destroy_index], limit=1, rules=self.destroy_rules)} overlaps buy rule {self._format_rule_index_list([buy_index], limit=1, rules=self.buy_rules)} on {self._format_compact_list([self._format_model_label(model_id) for model_id in overlap_ids], limit=2)}. Post-destroy inventory is what buy planning will maintain."
                    )

        return diagnostics

    def _draw_rule_overlap_diagnostics(self, messages: list[str]):
        if not messages:
            return
        self._draw_section_heading("Diagnostics")
        PyImGui.text_colored(
            "Potential rule overlap detected. Hard protections win first; otherwise earlier sell rules claim matching items.",
            UI_COLOR_WARNING,
        )
        for message in messages[:6]:
            self._draw_secondary_text(message)
        if len(messages) > 6:
            self._draw_secondary_text(f"...and {len(messages) - 6} more overlap warning(s).", wrapped=False)

    def _get_action_block_reason(self, action: str) -> str:
        busy = self.execution_running or self.travel_preview_running or self.instant_destroy_running or self.storage_scan_running or self.auto_cleanup_running
        if action == "preview":
            return "Merchant Rules is already busy." if busy else ""
        if action == "travel_preview":
            if busy:
                return "Preview, cleanup, or execution is already running."
            if not self.auto_travel_enabled:
                return "Enable Auto Travel to use Travel + Preview."
            if self.target_outpost_id <= 0:
                return "Choose a target outpost for Travel + Preview."
            return ""
        if action == "execute":
            if busy:
                return "Merchant Rules is already busy."
            if not self.preview_ready:
                return "Run Preview before executing merchant actions."
            if (
                self.preview_plan.travel_to_outpost_id <= 0
                and not self.preview_plan.supported_map
                and not self._plan_has_local_destroy_actions(self.preview_plan)
                and not self._plan_has_local_storage_actions(self.preview_plan)
            ):
                return self.preview_plan.supported_reason or "Current map is not supported for merchant handling."
            if not self.preview_plan.has_actions:
                return "Nothing is currently ready to execute."
            return ""
        if action == "execute_here":
            if busy:
                return "Merchant Rules is already busy."
            if not self.preview_ready:
                return "Run Preview before executing merchant actions here."
            actionable_here_count, _skipped_here_count = self._get_locally_actionable_preview_counts(self.preview_plan)
            if actionable_here_count <= 0:
                return "Nothing in the current preview is available to execute here."
            return ""
        if action == "cleanup":
            if busy:
                return "Merchant Rules is already busy."
            if not self._has_cleanup_sources():
                return "No Cleanup / Xunlai targets or linked sources are configured."
            if not Map.IsMapReady():
                return "Wait for the current map to finish loading."
            if not self._can_use_local_storage_actions():
                return "Run Cleanup Now requires an outpost or Guild Hall."
            return ""
        return ""

    def _has_any_rules(self) -> bool:
        return bool(self.buy_rules or self.sell_rules or self.destroy_rules or self._has_cleanup_sources())

    def _should_show_guided_empty_state(self) -> bool:
        return self.new_profile_session and not self._has_any_rules()

    def _append_buy_rule_of_kind(self, kind: str) -> bool:
        new_rule = BuyRule(kind=str(kind))
        normalized_rule = _normalize_buy_rule(new_rule)
        if normalized_rule is None:
            return False
        self.buy_rules.append(normalized_rule)
        self.active_buy_rule_kind = normalized_rule.kind
        self._refresh_rule_ui_caches()
        return True

    def _append_sell_rule_of_kind(self, kind: str) -> bool:
        new_rule = _normalize_sell_rule(SellRule(kind=str(kind)))
        if new_rule is None:
            return False
        self.sell_rules.append(new_rule)
        self._set_active_sell_rule_kind(new_rule.kind)
        self._refresh_rule_ui_caches()
        return True

    def _append_destroy_rule_of_kind(self, kind: str) -> bool:
        new_rule = _normalize_destroy_rule(DestroyRule(kind=str(kind)))
        self.destroy_rules.append(new_rule)
        self.active_destroy_rule_kind = new_rule.kind
        self._refresh_rule_ui_caches()
        return True

    def _add_buy_rule_of_kind(self, kind: str):
        if not self._append_buy_rule_of_kind(kind):
            return
        self._set_active_workspace(WORKSPACE_RULES)
        self._set_active_rules_workspace(RULES_WORKSPACE_BUY)
        self._save_profile()
        self._mark_preview_dirty("Buy rules changed. Preview again before execution.")

    def _add_sell_rule_of_kind(self, kind: str):
        if not self._append_sell_rule_of_kind(kind):
            return
        self._set_active_workspace(WORKSPACE_RULES)
        self._set_active_rules_workspace(RULES_WORKSPACE_SELL)
        self._save_profile()
        self._mark_preview_dirty("Sell rules changed. Preview again before execution.")

    def _add_destroy_rule_of_kind(self, kind: str):
        if not self._append_destroy_rule_of_kind(kind):
            return
        self._set_active_workspace(WORKSPACE_RULES)
        self._set_active_rules_workspace(RULES_WORKSPACE_DESTROY)
        self._save_profile()
        self._mark_preview_dirty("Destroy rules changed. Preview again before execution.")

    def _is_multibox_batch_running(self) -> bool:
        return bool(self.multibox_running_accounts)

    def _next_multibox_request_id(self, action: str) -> str:
        self.multibox_request_counter += 1
        return f"{str(action or 'merchant').strip()}_{int(time.time() * 1000)}_{self.multibox_request_counter}"

    def _get_account_display_name(self, account) -> str:
        character_name = str(getattr(getattr(account, "AgentData", None), "CharacterName", "") or "").strip()
        if character_name:
            return character_name
        return str(getattr(account, "AccountEmail", "") or "").strip() or "Unknown Account"

    def _get_account_party_position(self, account) -> int:
        try:
            return int(getattr(getattr(account, "AgentPartyData", None), "PartyPosition", 9999) or 9999)
        except Exception:
            return 9999

    def _get_account_party_id(self, account) -> int:
        try:
            return int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0)
        except Exception:
            return 0

    def _get_account_map_tuple(self, account) -> tuple[int, int, int, int]:
        agent_map = getattr(getattr(account, "AgentData", None), "Map", None)
        map_id = _safe_int(getattr(agent_map, "MapID", getattr(account, "MapID", 0)), 0)
        region = _safe_int(getattr(agent_map, "Region", getattr(account, "MapRegion", 0)), 0)
        district = _safe_int(getattr(agent_map, "District", getattr(account, "MapDistrict", 0)), 0)
        language = _safe_int(getattr(agent_map, "Language", getattr(account, "MapLanguage", 0)), 0)
        return map_id, region, district, language

    def _is_same_map_as_account(self, account) -> bool:
        own_map = int(Map.GetMapID() or 0)
        own_region = _safe_int(Map.GetRegion()[0] if Map.GetRegion() else 0, 0)
        own_district = _safe_int(Map.GetDistrict(), 0)
        own_language = _safe_int(Map.GetLanguage()[0] if Map.GetLanguage() else 0, 0)
        account_map = self._get_account_map_tuple(account)
        return account_map == (own_map, own_region, own_district, own_language)

    def _is_same_party_as_account(self, account) -> bool:
        own_party_id = _safe_int(GLOBAL_CACHE.Party.GetPartyID(), 0)
        return own_party_id > 0 and own_party_id == self._get_account_party_id(account)

    def _get_multibox_accounts(self) -> list[object]:
        own_email = _normalize_multibox_account_email(Player.GetAccountEmail())
        accounts: list[object] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_email = str(getattr(account, "AccountEmail", "") or "").strip()
            normalized_email = _normalize_multibox_account_email(account_email)
            if not normalized_email or normalized_email == own_email:
                continue
            if not bool(getattr(account, "IsSlotActive", False)):
                continue
            if bool(getattr(account, "IsHero", False)):
                continue
            accounts.append(account)
        accounts.sort(key=lambda account: (self._get_account_party_position(account), self._get_account_display_name(account).lower()))
        return accounts

    def _get_multibox_active_email_map(self) -> dict[str, str]:
        email_map: dict[str, str] = {}
        for account in self._get_multibox_accounts():
            account_email = str(getattr(account, "AccountEmail", "") or "").strip()
            normalized_email = _normalize_multibox_account_email(account_email)
            if normalized_email and normalized_email not in email_map:
                email_map[normalized_email] = account_email
        return email_map

    def _get_multibox_display_name_from_email(self, account_email: str) -> str:
        raw_email = str(account_email or "").strip()
        normalized_email = _normalize_multibox_account_email(account_email)
        for account in self._get_multibox_accounts():
            if _normalize_multibox_account_email(getattr(account, "AccountEmail", "")) == normalized_email:
                return self._get_account_display_name(account)
        return raw_email or normalized_email or "Unknown Account"

    def _get_selected_multibox_emails(self) -> list[str]:
        active_email_map = self._get_multibox_active_email_map()
        return [
            actual_email
            for normalized_email, actual_email in active_email_map.items()
            if self.multibox_selected_accounts.get(normalized_email, False)
        ]

    def _set_multibox_status(
        self,
        account_email: str,
        *,
        state: str,
        status_label: str = "",
        summary: str = "",
        detail: str = "",
        primary_count: int = 0,
        secondary_count: int = 0,
        success: bool = False,
    ):
        normalized_email = _normalize_multibox_account_email(account_email)
        if not normalized_email:
            return
        status = self.multibox_statuses.get(normalized_email)
        if status is None:
            status = MultiboxAccountStatus(
                email=normalized_email,
                display_name=self._get_multibox_display_name_from_email(normalized_email),
            )
            self.multibox_statuses[normalized_email] = status
        else:
            status.display_name = self._get_multibox_display_name_from_email(normalized_email) or status.display_name
        status.state = str(state or "idle")
        status.status_label = str(status_label or "").strip()
        status.summary = str(summary or "").strip()
        status.detail = str(detail or "").strip()
        status.primary_count = max(0, int(primary_count))
        status.secondary_count = max(0, int(secondary_count))
        status.success = bool(success)

    def _clear_multibox_batch_runtime(self):
        self.multibox_pending_accounts = []
        self.multibox_running_email = ""
        self.multibox_running_started_at_ms = 0
        self.multibox_running_accounts = {}

    def _send_multibox_command(
        self,
        receiver_email: str,
        opcode: int,
        request_id: str,
        status_label: str,
        extra2: str = "",
        extra3: str = "",
    ):
        sender_email = str(Player.GetAccountEmail() or "").strip()
        target_email = str(receiver_email or "").strip()
        if not sender_email or not target_email:
            self._debug_log(
                f"Merchant Rules multibox send skipped: sender={sender_email!r} receiver={target_email!r} opcode={int(opcode)} request_id={request_id}"
            )
            return False
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            target_email,
            SharedCommandType.MerchantRules,
            (float(opcode), 0.0, 0.0, 0.0),
            (request_id, status_label, str(extra2 or ""), str(extra3 or "")),
        )
        if message_index == -1:
            self._debug_log(
                f"Merchant Rules multibox send failed: sender={sender_email} receiver={target_email} opcode={int(opcode)} "
                f"request_id={request_id} label={status_label}"
            )
            return False
        self._debug_log(
            f"Merchant Rules multibox send queued: sender={sender_email} receiver={target_email} opcode={int(opcode)} "
            f"request_id={request_id} label={status_label} index={message_index}"
        )
        return True

    def _start_multibox_sync(self):
        selected_emails = self._get_selected_multibox_emails()
        if not selected_emails:
            return
        self.multibox_active_action = "sync"
        self.multibox_active_request_id = self._next_multibox_request_id("sync")
        self._clear_multibox_batch_runtime()
        payload = self._build_profile_payload(include_window_geometry=False)
        for account_email in selected_emails:
            self._set_multibox_status(
                account_email,
                state="running",
                status_label="Syncing",
                summary="Writing leader live config to follower config.",
            )
            try:
                self._write_profile_payload_for_account(
                    account_email,
                    payload,
                    preserve_existing_window_geometry=True,
                )
                send_succeeded = self._send_multibox_command(
                    account_email,
                    MERCHANT_RULES_OPCODE_RELOAD_PROFILE,
                    self.multibox_active_request_id,
                    "Sync",
                )
                if send_succeeded:
                    self._set_multibox_status(
                        account_email,
                        state="synced",
                        status_label="Synced",
                        summary="Live config written and reload requested.",
                        success=True,
                    )
                else:
                    self._set_multibox_status(
                        account_email,
                        state="error",
                        status_label="Reload Not Queued",
                        summary="Live config was written, but the follower reload request was not queued.",
                        detail="Shared-memory send failed before enqueue.",
                        success=False,
                    )
            except Exception as exc:
                self._set_multibox_status(
                    account_email,
                    state="error",
                    status_label="Sync Failed",
                    summary="Could not sync Merchant Rules live config.",
                    detail=str(exc),
                    success=False,
                )

    def _start_multibox_batch(self, action: str, opcode: int):
        selected_emails = self._get_selected_multibox_emails()
        if not selected_emails:
            return
        self.multibox_active_action = str(action or "").strip() or "preview"
        self.multibox_active_request_id = self._next_multibox_request_id(self.multibox_active_action)
        self._clear_multibox_batch_runtime()
        include_protected_flag = "1" if self.destroy_include_protected_items else "0"
        instant_destroy_flag = "1" if self.destroy_instant_enabled else "0"
        if opcode == MERCHANT_RULES_OPCODE_PREVIEW:
            active_email_map = self._get_multibox_active_email_map()
            started_at_ms = int(time.time() * 1000)
            for account_email in selected_emails:
                normalized_email = _normalize_multibox_account_email(account_email)
                target_email = active_email_map.get(normalized_email, "")
                if not target_email:
                    self._set_multibox_status(
                        account_email,
                        state="error",
                        status_label="Unavailable",
                        summary="Selected account is no longer active.",
                        success=False,
                    )
                    continue
                send_succeeded = self._send_multibox_command(
                    target_email,
                    MERCHANT_RULES_OPCODE_PREVIEW,
                    self.multibox_active_request_id,
                    "Preview",
                    include_protected_flag,
                    instant_destroy_flag,
                )
                if not send_succeeded:
                    self._set_multibox_status(
                        account_email,
                        state="error",
                        status_label="Request Not Queued",
                        summary="Remote preview request was not queued.",
                        detail="Shared-memory send failed before enqueue.",
                        success=False,
                    )
                    continue
                self.multibox_running_accounts[normalized_email] = started_at_ms
                self._set_multibox_status(
                    account_email,
                    state="running",
                    status_label="Running",
                    summary="Remote preview in progress.",
                    success=False,
                )
            return

        active_email_map = self._get_multibox_active_email_map()
        started_at_ms = int(time.time() * 1000)
        for account_email in selected_emails:
            normalized_email = _normalize_multibox_account_email(account_email)
            target_email = active_email_map.get(normalized_email, "")
            if not target_email:
                self._set_multibox_status(
                    account_email,
                    state="error",
                    status_label="Unavailable",
                    summary="Selected account is no longer active.",
                    success=False,
                )
                continue
            send_succeeded = self._send_multibox_command(
                target_email,
                MERCHANT_RULES_OPCODE_EXECUTE,
                self.multibox_active_request_id,
                "Execute",
                include_protected_flag,
                instant_destroy_flag,
            )
            if not send_succeeded:
                self._set_multibox_status(
                    account_email,
                    state="error",
                    status_label="Request Not Queued",
                    summary="Remote execute request was not queued.",
                    detail="Shared-memory send failed before enqueue.",
                    success=False,
                )
                continue
            self.multibox_running_accounts[normalized_email] = started_at_ms
            self._set_multibox_status(
                account_email,
                state="pending",
                status_label="Queued",
                summary="Remote execute request queued.",
                success=False,
            )

    def _advance_multibox_batch(self):
        if self.multibox_active_action not in ("preview", "execute"):
            return
        current_time_ms = int(time.time() * 1000)
        if self.multibox_active_action == "execute" and self.multibox_running_email:
            elapsed_ms = max(0, current_time_ms - int(self.multibox_running_started_at_ms))
            if elapsed_ms >= MULTIBOX_REMOTE_TIMEOUT_MS:
                timed_out_email = self.multibox_running_email
                normalized_timeout_email = _normalize_multibox_account_email(timed_out_email)
                self.multibox_running_email = ""
                self.multibox_running_started_at_ms = 0
                self.multibox_running_accounts.pop(normalized_timeout_email, None)
                self._debug_log(
                    f"Merchant Rules multibox timeout: action=execute follower={normalized_timeout_email} "
                    f"request_id={self.multibox_active_request_id}"
                )
                self._set_multibox_status(
                    timed_out_email,
                    state="error",
                    status_label="Timed Out",
                    summary="No response received from follower.",
                    detail="The follower did not answer the Merchant Rules request in time.",
                    success=False,
                )

        timeout_ms = (
            MULTIBOX_EXECUTE_REMOTE_TIMEOUT_MS
            if self.multibox_active_action == "execute"
            else MULTIBOX_REMOTE_TIMEOUT_MS
        )
        for normalized_email, last_update_at_ms in list(self.multibox_running_accounts.items()):
            elapsed_ms = max(0, current_time_ms - int(last_update_at_ms))
            if elapsed_ms < timeout_ms:
                continue
            self.multibox_running_accounts.pop(normalized_email, None)
            self._debug_log(
                f"Merchant Rules multibox timeout: action={self.multibox_active_action} follower={normalized_email} "
                f"request_id={self.multibox_active_request_id}"
            )
            detail = (
                "The follower did not report execute progress or completion in time."
                if self.multibox_active_action == "execute"
                else "The follower did not answer the Merchant Rules preview request in time."
            )
            self._set_multibox_status(
                normalized_email,
                state="error",
                status_label="Timed Out",
                summary="No response received from follower.",
                detail=detail,
                success=False,
            )

        if self.multibox_active_action == "execute" and not self.multibox_running_email and self.multibox_pending_accounts:
            active_email_map = self._get_multibox_active_email_map()
            include_protected_flag = "1" if self.destroy_include_protected_items else "0"
            instant_destroy_flag = "1" if self.destroy_instant_enabled else "0"
            pending_accounts = list(self.multibox_pending_accounts)
            self.multibox_pending_accounts = []
            for index, account_email in enumerate(pending_accounts):
                normalized_email = _normalize_multibox_account_email(account_email)
                target_email = active_email_map.get(normalized_email, "")
                if not target_email:
                    self._set_multibox_status(
                        account_email,
                        state="error",
                        status_label="Unavailable",
                        summary="Selected account is no longer active.",
                        success=False,
                    )
                    continue
                send_succeeded = self._send_multibox_command(
                    target_email,
                    MERCHANT_RULES_OPCODE_EXECUTE,
                    self.multibox_active_request_id,
                    "Execute",
                    include_protected_flag,
                    instant_destroy_flag,
                )
                if not send_succeeded:
                    self._set_multibox_status(
                        account_email,
                        state="error",
                        status_label="Request Not Queued",
                        summary="Remote execute request was not queued.",
                        detail="Shared-memory send failed before enqueue.",
                        success=False,
                    )
                    continue
                self.multibox_running_email = normalized_email
                self.multibox_running_started_at_ms = current_time_ms
                self.multibox_running_accounts[normalized_email] = current_time_ms
                self._set_multibox_status(
                    account_email,
                    state="running",
                    status_label="Running",
                    summary="Remote execute in progress.",
                    success=False,
                )
                self.multibox_pending_accounts = pending_accounts[index + 1 :]
                break

    def _get_multibox_state_color(self, status: MultiboxAccountStatus) -> tuple[float, float, float, float]:
        if status.state in ("error", "failed"):
            return UI_COLOR_DANGER
        if status.state in ("synced", "preview_result", "execute_result"):
            return UI_COLOR_SUCCESS if status.success else UI_COLOR_WARNING
        if status.state in ("running", "starting"):
            return UI_COLOR_INFO
        if status.state in ("pending", "waiting"):
            return UI_COLOR_WARNING
        return UI_COLOR_MUTED

    def _get_multibox_plan_counts(self, plan: PlanResult) -> tuple[int, int]:
        actionable_entries, skipped_entries = self._split_preview_entries(plan.entries)
        return len(actionable_entries), len(skipped_entries)

    def _extract_multibox_message_extra_data(self, message) -> tuple[str, str, str, str]:
        values: list[str] = []
        for raw in getattr(message, "ExtraData", ()):
            try:
                values.append("".join(ch for ch in raw if ch != "\0").rstrip())
            except Exception:
                values.append("")
        while len(values) < 4:
            values.append("")
        return tuple(values[:4])

    def _get_multibox_message_opcode(self, message) -> int:
        try:
            return _safe_int(message.Params[0], 0)
        except Exception:
            return 0

    def _is_multibox_result_opcode(self, opcode: int) -> bool:
        return opcode in (
            MERCHANT_RULES_OPCODE_STATUS_RESULT,
            MERCHANT_RULES_OPCODE_PREVIEW_RESULT,
            MERCHANT_RULES_OPCODE_EXECUTE_RESULT,
            MERCHANT_RULES_OPCODE_ERROR_RESULT,
        )

    def _multibox_message_requires_merchant_lock(self, message) -> bool:
        opcode = self._get_multibox_message_opcode(message)
        return opcode == MERCHANT_RULES_OPCODE_EXECUTE

    def _compact_multibox_message_text(self, value: object, limit: int = 60) -> str:
        text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)].rstrip() + "..."

    def _snapshot_multibox_hero_ai_options(self, account_email: str) -> dict[str, bool] | None:
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if hero_ai_options is None:
            return None
        return {
            "Following": bool(hero_ai_options.Following),
            "Avoidance": bool(hero_ai_options.Avoidance),
            "Looting": bool(hero_ai_options.Looting),
            "Targeting": bool(hero_ai_options.Targeting),
            "Combat": bool(hero_ai_options.Combat),
        }

    def _disable_multibox_hero_ai_options(self, account_email: str):
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if hero_ai_options is None:
            return
        hero_ai_options.Following = False
        hero_ai_options.Avoidance = False
        hero_ai_options.Looting = False
        hero_ai_options.Targeting = False
        hero_ai_options.Combat = False

    def _enable_multibox_hero_ai_options(self, account_email: str):
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if hero_ai_options is None:
            return
        hero_ai_options.Following = True
        hero_ai_options.Avoidance = True
        hero_ai_options.Looting = True
        hero_ai_options.Targeting = True
        hero_ai_options.Combat = True

    def _restore_multibox_hero_ai_options(self, account_email: str, snapshot: dict[str, bool] | None):
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if hero_ai_options is None:
            return
        if snapshot is None:
            self._enable_multibox_hero_ai_options(account_email)
            return
        hero_ai_options.Following = bool(snapshot.get("Following", True))
        hero_ai_options.Avoidance = bool(snapshot.get("Avoidance", True))
        hero_ai_options.Looting = bool(snapshot.get("Looting", True))
        hero_ai_options.Targeting = bool(snapshot.get("Targeting", True))
        hero_ai_options.Combat = bool(snapshot.get("Combat", True))

    def _send_multibox_status_message(
        self,
        receiver_email: str,
        *,
        request_id: str,
        status_label: str,
        summary: str,
        detail: str = "",
        primary_count: int = 0,
        secondary_count: int = 0,
    ):
        return self._send_multibox_result_message(
            receiver_email,
            request_id=request_id,
            opcode=MERCHANT_RULES_OPCODE_STATUS_RESULT,
            primary_count=primary_count,
            secondary_count=secondary_count,
            success_flag=False,
            status_label=status_label,
            summary=summary,
            detail=detail,
        )

    def _send_multibox_status_from_message(
        self,
        message,
        *,
        status_label: str,
        summary: str,
        detail: str = "",
        primary_count: int = 0,
        secondary_count: int = 0,
    ):
        extra0, _extra1, _extra2, _extra3 = self._extract_multibox_message_extra_data(message)
        request_id = str(extra0 or "").strip()
        sender_email = str(getattr(message, "SenderEmail", "") or "").strip()
        if not sender_email:
            return False
        return self._send_multibox_status_message(
            sender_email,
            request_id=request_id,
            status_label=status_label,
            summary=summary,
            detail=detail,
            primary_count=primary_count,
            secondary_count=secondary_count,
        )

    def _get_remote_execute_wait_reason(self) -> str:
        if self.execution_running:
            return "Merchant Rules execution is already running."
        if self.travel_preview_running:
            return "Merchant Rules Travel + Preview is already running."
        if self.instant_destroy_running:
            return "Merchant Rules Instant Destroy is already running."
        if self.storage_scan_running:
            return "Merchant Rules exact storage scan is already running."
        if self.auto_cleanup_running:
            return "Merchant Rules Cleanup / Xunlai is already running."
        if not Map.IsMapReady():
            return "Current map is still loading."
        return ""

    def _wait_for_remote_execute_start(
        self,
        message,
        *,
        is_merchant_busy: Callable[[], bool] | None = None,
        timeout_ms: int = MULTIBOX_REMOTE_IDLE_WAIT_TIMEOUT_MS,
        step_ms: int = 250,
    ):
        waited_ms = 0
        last_wait_reason = ""
        last_status_sent_at_ms = 0
        while waited_ms < max(0, int(timeout_ms)):
            wait_reason = self._get_remote_execute_wait_reason()
            if not wait_reason and callable(is_merchant_busy) and bool(is_merchant_busy()):
                wait_reason = "Another merchant action is already running on this client."
            if not wait_reason:
                return True
            current_time_ms = int(time.time() * 1000)
            if (
                wait_reason != last_wait_reason
                or current_time_ms - last_status_sent_at_ms >= MULTIBOX_REMOTE_STATUS_UPDATE_INTERVAL_MS
            ):
                self._send_multibox_status_from_message(
                    message,
                    status_label="Waiting",
                    summary="Remote execute is waiting for the follower to become idle.",
                    detail=wait_reason,
                )
                last_wait_reason = wait_reason
                last_status_sent_at_ms = current_time_ms
            waited_ms += max(1, int(step_ms))
            yield from Routines.Yield.wait(step_ms)

        timeout_reason = self._get_remote_execute_wait_reason()
        if not timeout_reason and callable(is_merchant_busy) and bool(is_merchant_busy()):
            timeout_reason = "Another merchant action is still running on this client."
        timeout_label = "Map Not Ready" if not Map.IsMapReady() else "Busy Timeout"
        self._send_multibox_result_message(
            str(getattr(message, "SenderEmail", "") or "").strip(),
            request_id=str(self._extract_multibox_message_extra_data(message)[0] or "").strip(),
            opcode=MERCHANT_RULES_OPCODE_ERROR_RESULT,
            primary_count=0,
            secondary_count=1,
            success_flag=False,
            status_label=timeout_label,
            summary="Remote execute did not start before timeout.",
            detail=timeout_reason or "The follower did not become ready for Merchant Rules execution in time.",
        )
        return False

    def _send_multibox_result_message(
        self,
        receiver_email: str,
        *,
        request_id: str,
        opcode: int,
        primary_count: int,
        secondary_count: int,
        success_flag: bool,
        status_label: str,
        summary: str,
        detail: str,
    ):
        sender_email = str(Player.GetAccountEmail() or "").strip()
        target_email = str(receiver_email or "").strip()
        if not sender_email or not target_email:
            self._debug_log(
                f"Merchant Rules multibox result skipped: sender={sender_email!r} receiver={target_email!r} "
                f"opcode={int(opcode)} request_id={request_id}"
            )
            return False
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            target_email,
            SharedCommandType.MerchantRules,
            (
                float(opcode),
                float(max(0, int(primary_count))),
                float(max(0, int(secondary_count))),
                1.0 if success_flag else 0.0,
            ),
            (
                self._compact_multibox_message_text(request_id, 60),
                self._compact_multibox_message_text(status_label, 60),
                self._compact_multibox_message_text(summary, 60),
                self._compact_multibox_message_text(detail, 60),
            ),
        )
        if message_index == -1:
            self._debug_log(
                f"Merchant Rules multibox result failed: sender={sender_email} receiver={target_email} opcode={int(opcode)} "
                f"request_id={request_id} label={status_label} summary={summary}"
            )
            return False
        self._debug_log(
            f"Merchant Rules multibox result queued: sender={sender_email} receiver={target_email} opcode={int(opcode)} "
            f"request_id={request_id} label={status_label} summary={summary} index={message_index}"
        )
        return True

    def handle_shared_multibox_message(self, message):
        extra0, extra1, extra2, extra3 = self._extract_multibox_message_extra_data(message)
        request_id = str(extra0 or "").strip()
        sender_email = str(getattr(message, "SenderEmail", "") or "").strip()
        receiver_email = str(getattr(message, "ReceiverEmail", "") or Player.GetAccountEmail() or "").strip()
        opcode = self._get_multibox_message_opcode(message)
        requested_include_protected = str(extra2 or "").strip() == "1"
        requested_instant_destroy = str(extra3 or "").strip() == "1"
        self._debug_log(
            f"Merchant Rules multibox receive: sender={sender_email or '<missing>'} receiver={receiver_email or '<missing>'} "
            f"opcode={int(opcode)} request_id={request_id}"
        )
        try:
            primary_count = _safe_int(message.Params[1], 0)
        except Exception:
            primary_count = 0
        try:
            secondary_count = _safe_int(message.Params[2], 0)
        except Exception:
            secondary_count = 0
        try:
            success_flag = bool(_safe_int(message.Params[3], 0))
        except Exception:
            success_flag = False

        if self._is_multibox_result_opcode(opcode):
            self.handle_multibox_result(
                sender_email,
                request_id=request_id,
                opcode=opcode,
                primary_count=primary_count,
                secondary_count=secondary_count,
                success_flag=success_flag,
                status_label=extra1,
                summary=extra2,
                detail=extra3,
            )
            return

        if opcode == MERCHANT_RULES_OPCODE_RELOAD_PROFILE:
            self.reload_profile_from_disk(
                status_message="Merchant Rules live config reloaded by multibox sync.",
                preserve_window_geometry=True,
            )
            return

        hero_ai_snapshot: dict[str, bool] | None = None
        original_include_protected = False
        original_instant_destroy = False
        restore_destroy_session_state = False
        try:
            if opcode == MERCHANT_RULES_OPCODE_PREVIEW:
                self._ensure_initialized()
                original_include_protected = bool(self.destroy_include_protected_items)
                original_instant_destroy = bool(self.destroy_instant_enabled)
                hero_ai_snapshot = self._snapshot_multibox_hero_ai_options(receiver_email)
                self._disable_multibox_hero_ai_options(receiver_email)
                self.destroy_include_protected_items = requested_include_protected
                self.destroy_instant_enabled = requested_instant_destroy
                restore_destroy_session_state = True
                yield from Routines.Yield.wait(100)

            if opcode == MERCHANT_RULES_OPCODE_PREVIEW:
                self._scan_preview()
                result = self.build_remote_preview_result()
                self._send_multibox_result_message(
                    sender_email,
                    request_id=request_id,
                    opcode=int(result.get("opcode", MERCHANT_RULES_OPCODE_PREVIEW_RESULT)),
                    primary_count=int(result.get("primary_count", 0)),
                    secondary_count=int(result.get("secondary_count", 0)),
                    success_flag=bool(result.get("success", True)),
                    status_label=str(result.get("status_label", "")),
                    summary=str(result.get("summary", "")),
                    detail=str(result.get("detail", "")),
                )
            elif opcode == MERCHANT_RULES_OPCODE_EXECUTE:
                self._ensure_initialized()
                original_include_protected = bool(self.destroy_include_protected_items)
                original_instant_destroy = bool(self.destroy_instant_enabled)
                hero_ai_snapshot = self._snapshot_multibox_hero_ai_options(receiver_email)
                self._disable_multibox_hero_ai_options(receiver_email)
                self.destroy_include_protected_items = requested_include_protected
                self.destroy_instant_enabled = requested_instant_destroy
                restore_destroy_session_state = True
                yield from Routines.Yield.wait(100)
                self._send_multibox_status_message(
                    sender_email,
                    request_id=request_id,
                    status_label="Starting",
                    summary="Remote execute is starting.",
                )
                yield from self._execute_now()
                if str(self.last_error or "").strip():
                    self._send_multibox_result_message(
                        sender_email,
                        request_id=request_id,
                        opcode=MERCHANT_RULES_OPCODE_ERROR_RESULT,
                        primary_count=0,
                        secondary_count=1,
                        success_flag=False,
                        status_label="Execute Failed",
                        summary="Merchant Rules execution failed.",
                        detail=str(self.last_error or self.status_message or ""),
                    )
                else:
                    result = self.build_remote_execute_result()
                    self._send_multibox_result_message(
                        sender_email,
                        request_id=request_id,
                        opcode=int(result.get("opcode", MERCHANT_RULES_OPCODE_EXECUTE_RESULT)),
                        primary_count=int(result.get("primary_count", 0)),
                        secondary_count=int(result.get("secondary_count", 0)),
                        success_flag=bool(result.get("success", True)),
                        status_label=str(result.get("status_label", "")),
                        summary=str(result.get("summary", "")),
                        detail=str(result.get("detail", "")),
                    )
            else:
                self._send_multibox_result_message(
                    sender_email,
                    request_id=request_id,
                    opcode=MERCHANT_RULES_OPCODE_ERROR_RESULT,
                    primary_count=0,
                    secondary_count=1,
                    success_flag=False,
                    status_label="Unknown Opcode",
                    summary="Merchant Rules command was not recognized.",
                    detail=f"Unsupported opcode: {opcode}",
                )
        except Exception as exc:
            ConsoleLog(MODULE_NAME, f"Merchant Rules multibox error: {exc}", Console.MessageType.Error)
            ConsoleLog(MODULE_NAME, traceback.format_exc(), Console.MessageType.Error)
            self._send_multibox_result_message(
                sender_email,
                request_id=request_id,
                opcode=MERCHANT_RULES_OPCODE_ERROR_RESULT,
                primary_count=0,
                secondary_count=1,
                success_flag=False,
                status_label="Error",
                summary="Merchant Rules remote handling failed.",
                detail=str(exc),
            )
        finally:
            if opcode in (MERCHANT_RULES_OPCODE_PREVIEW, MERCHANT_RULES_OPCODE_EXECUTE):
                self._restore_multibox_hero_ai_options(receiver_email, hero_ai_snapshot)
            if restore_destroy_session_state:
                self.destroy_include_protected_items = original_include_protected
                self.destroy_instant_enabled = original_instant_destroy

    def build_remote_preview_result(self) -> dict[str, object]:
        self._ensure_initialized()
        direct_count, conditional_count, skipped_count = self._get_preview_entry_counts(self.preview_plan.entries)
        actionable_count = direct_count + conditional_count
        local_destroy_ready = self._plan_has_local_destroy_actions(self.preview_plan)
        local_storage_ready = self._plan_has_local_storage_actions(self.preview_plan)
        conditional_cleanup_ready = self._plan_has_conditional_cleanup_actions(self.preview_plan)
        projected_preview = self._preview_has_execute_travel_pending()
        if actionable_count > 0:
            if projected_preview:
                status_label = "Projected"
            elif not self.preview_plan.supported_map and local_destroy_ready and not local_storage_ready:
                status_label = "Destroy Ready"
            else:
                status_label = "Conditional" if direct_count <= 0 and conditional_count > 0 else "Ready"
            summary_parts = [f"{actionable_count} actionable", f"{skipped_count} blocked"]
            if conditional_count > 0:
                summary_parts.append(f"{conditional_count} conditional")
            summary = ", ".join(summary_parts) + "."
        elif projected_preview:
            status_label = "No Actions"
            summary = "No actionable merchant work found."
        elif not self.preview_plan.supported_map:
            status_label = "Unsupported"
            summary = self.preview_plan.supported_reason or "Current map is not supported."
        else:
            status_label = "No Actions"
            summary = "No actionable merchant work found."

        if projected_preview:
            target_label = self.preview_execute_travel_target_outpost_name or "the selected outpost"
            detail_parts = [
                f"Projected after travel to {target_label}. Travel + Execute will auto-travel and rebuild live merchant handling on arrival.",
            ]
            if self._plan_needs_exact_storage_scan(self.preview_plan):
                detail_parts.append("Storage-aware rune planning is still partial until Xunlai is opened for an exact storage scan.")
            elif conditional_cleanup_ready:
                detail_parts.append("Planned Xunlai cleanup work will execute if storage can be opened after arrival.")
            elif conditional_count > 0:
                detail_parts.append("Conditional entries remain estimated until the destination context is confirmed.")
            detail = " ".join(detail_parts).strip()
        elif actionable_count > 0 and not self.preview_plan.supported_map and local_destroy_ready and local_storage_ready:
            detail = (
                "Merchant NPCs are unavailable here, but local destroy actions and Xunlai cleanup work are still ready."
                if not conditional_cleanup_ready
                else "Merchant NPCs are unavailable here, but planned Xunlai cleanup work will run if storage can be opened."
            )
        elif actionable_count > 0 and not self.preview_plan.supported_map and local_destroy_ready:
            detail = "Merchant NPCs are unavailable here, but local destroy actions are still ready."
        elif actionable_count > 0 and not self.preview_plan.supported_map and local_storage_ready:
            detail = (
                "Merchant NPCs are unavailable here, but Xunlai cleanup work is still ready."
                if not conditional_cleanup_ready
                else "Merchant NPCs are unavailable here, but planned Xunlai cleanup work will run if storage can be opened."
            )
        elif not self.preview_plan.supported_map:
            detail = self.preview_plan.supported_reason or self.status_message or "Current map is not supported."
        elif self._plan_needs_exact_storage_scan(self.preview_plan):
            detail = "Storage-aware planning is still partial until Xunlai is opened for an exact storage scan."
        elif conditional_cleanup_ready:
            detail = "Planned Xunlai cleanup work will execute if storage can be opened at runtime."
        elif conditional_count > 0:
            detail = "Conditional actions need live merchant or trader confirmation at runtime."
        elif actionable_count > 0:
            detail = self.status_message or self.preview_plan.supported_reason
        else:
            detail = self.status_message or self.preview_plan.supported_reason or summary
        return {
            "opcode": MERCHANT_RULES_OPCODE_PREVIEW_RESULT,
            "primary_count": actionable_count,
            "secondary_count": skipped_count,
            "success": True,
            "status_label": status_label,
            "summary": summary,
            "detail": detail,
        }

    def build_remote_execute_result(self) -> dict[str, object]:
        self._ensure_initialized()
        primary_count, secondary_count = self._get_multibox_plan_counts(self.preview_plan)
        if primary_count > 0:
            status_label = "Executed"
            summary = self.last_execution_summary or f"Executed {primary_count} action(s)."
        else:
            status_label = "No Actions"
            summary = self.status_message or "Nothing was executed."
        return {
            "opcode": MERCHANT_RULES_OPCODE_EXECUTE_RESULT,
            "primary_count": primary_count,
            "secondary_count": secondary_count,
            "success": True,
            "status_label": status_label,
            "summary": summary,
            "detail": self.status_message,
        }

    def handle_multibox_result(
        self,
        sender_email: str,
        *,
        request_id: str,
        opcode: int,
        primary_count: int,
        secondary_count: int,
        success_flag: bool,
        status_label: str,
        summary: str,
        detail: str,
    ) -> bool:
        normalized_email = _normalize_multibox_account_email(sender_email)
        if not normalized_email:
            return False
        if request_id and self.multibox_active_request_id and request_id != self.multibox_active_request_id:
            self._debug_log(
                f"Ignored Merchant Rules multibox result from {normalized_email}: request_id={request_id} current={self.multibox_active_request_id}"
            )
            return False

        current_time_ms = int(time.time() * 1000)
        if opcode == MERCHANT_RULES_OPCODE_STATUS_RESULT:
            status_key = str(status_label or "").strip().lower()
            state = "running"
            if status_key == "waiting":
                state = "waiting"
            elif status_key == "starting":
                state = "starting"
            self.multibox_running_accounts[normalized_email] = current_time_ms
            self._set_multibox_status(
                normalized_email,
                state=state,
                status_label=status_label or "Running",
                summary=summary,
                detail=detail,
                primary_count=primary_count,
                secondary_count=secondary_count,
                success=False,
            )
            self._debug_log(
                f"Accepted Merchant Rules multibox status from {normalized_email}: opcode={int(opcode)} "
                f"request_id={request_id} status={status_label}"
            )
            return True

        state = "preview_result"
        if opcode == MERCHANT_RULES_OPCODE_EXECUTE_RESULT:
            state = "execute_result"
        elif opcode == MERCHANT_RULES_OPCODE_ERROR_RESULT:
            state = "error"

        self._set_multibox_status(
            normalized_email,
            state=state,
            status_label=status_label or ("Error" if state == "error" else "Done"),
            summary=summary,
            detail=detail,
            primary_count=primary_count,
            secondary_count=secondary_count,
            success=bool(success_flag) and state != "error",
        )
        self._debug_log(
            f"Accepted Merchant Rules multibox result from {normalized_email}: opcode={int(opcode)} "
            f"request_id={request_id} status={status_label} success={bool(success_flag)}"
        )
        if normalized_email == _normalize_multibox_account_email(self.multibox_running_email):
            self.multibox_running_email = ""
            self.multibox_running_started_at_ms = 0
        self.multibox_running_accounts.pop(normalized_email, None)
        return True

    def _draw_multibox_section(self):
        self._draw_section_heading("Multibox")
        accounts = self._get_multibox_accounts()
        if not accounts:
            self._draw_secondary_text("No other active multibox accounts were detected.")
            return

        selected_emails = self._get_selected_multibox_emails()
        self._draw_secondary_text(f"{len(accounts)} active account(s) | {len(selected_emails)} selected", wrapped=False)
        if PyImGui.small_button("Select All##merchant_multibox_select_all"):
            for account in accounts:
                account_email = str(getattr(account, "AccountEmail", "") or "").strip()
                if account_email:
                    self.multibox_selected_accounts[_normalize_multibox_account_email(account_email)] = True
        PyImGui.same_line(0, 8)
        if PyImGui.small_button("Clear##merchant_multibox_select_clear"):
            for account in accounts:
                account_email = str(getattr(account, "AccountEmail", "") or "").strip()
                if account_email:
                    self.multibox_selected_accounts[_normalize_multibox_account_email(account_email)] = False

        child_height = min(180, 40 + (26 * len(accounts)))
        if PyImGui.begin_child("merchant_rules_multibox_accounts", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table("merchant_rules_multibox_accounts_table", 4, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV):
                PyImGui.table_setup_column("Use", PyImGui.TableColumnFlags.WidthFixed, 48.0)
                PyImGui.table_setup_column("Account", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Context", PyImGui.TableColumnFlags.WidthFixed, 180.0)
                PyImGui.table_setup_column("Status", PyImGui.TableColumnFlags.WidthStretch)
                for account in accounts:
                    account_email = str(getattr(account, "AccountEmail", "") or "").strip()
                    account_key = _normalize_multibox_account_email(account_email)
                    display_name = self._get_account_display_name(account)
                    status = self.multibox_statuses.get(account_key)
                    PyImGui.table_next_row()

                    PyImGui.table_set_column_index(0)
                    is_selected = bool(self.multibox_selected_accounts.get(account_key, False))
                    new_selected = PyImGui.checkbox(f"##merchant_multibox_select_{account_email}", is_selected)
                    if new_selected != is_selected:
                        self.multibox_selected_accounts[account_key] = bool(new_selected)

                    PyImGui.table_set_column_index(1)
                    PyImGui.text(display_name)
                    if account_email and account_email != display_name:
                        self._draw_secondary_text(account_email, wrapped=False)

                    PyImGui.table_set_column_index(2)
                    self._draw_inline_badge("Same Map" if self._is_same_map_as_account(account) else "Other Map", UI_COLOR_SUCCESS if self._is_same_map_as_account(account) else UI_COLOR_MUTED)
                    PyImGui.same_line(0, 6)
                    self._draw_inline_badge("Party" if self._is_same_party_as_account(account) else "No Party", UI_COLOR_INFO if self._is_same_party_as_account(account) else UI_COLOR_MUTED)

                    PyImGui.table_set_column_index(3)
                    if status is None:
                        self._draw_secondary_text("Idle", wrapped=False)
                    else:
                        self._draw_inline_badge(status.status_label or "Idle", self._get_multibox_state_color(status))
                        if status.summary:
                            PyImGui.same_line(0, 6)
                            self._draw_secondary_text(status.summary, wrapped=False)
                        if status.detail:
                            self._draw_secondary_text(status.detail)
                        elif status.primary_count > 0 or status.secondary_count > 0:
                            self._draw_secondary_text(
                                f"{status.primary_count} primary | {status.secondary_count} secondary",
                                wrapped=False,
                            )
                PyImGui.end_table()
        PyImGui.end_child()

        batch_running = self._is_multibox_batch_running()
        no_selection = not selected_emails
        PyImGui.begin_disabled(no_selection or batch_running)
        sync_clicked = PyImGui.button("Sync Rules To Selected")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(no_selection or batch_running)
        preview_clicked = PyImGui.button("Preview Selected")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(no_selection or batch_running)
        execute_clicked = PyImGui.button("Execute Selected")
        PyImGui.end_disabled()

        selected_statuses = [
            self.multibox_statuses.get(_normalize_multibox_account_email(email))
            for email in selected_emails
            if _normalize_multibox_account_email(email)
        ]
        waiting_count = sum(1 for status in selected_statuses if status is not None and status.state in ("pending", "waiting"))
        running_count = sum(1 for status in selected_statuses if status is not None and status.state in ("starting", "running"))
        finished_count = sum(
            1
            for status in selected_statuses
            if status is not None and status.state in ("preview_result", "execute_result", "synced")
        )
        error_count = sum(1 for status in selected_statuses if status is not None and status.state == "error")

        if batch_running and self.multibox_active_action == "preview":
            self._draw_secondary_text(
                f"Remote preview progress: {running_count} running | {finished_count} finished | {error_count} issue(s)."
            )
        elif batch_running and self.multibox_active_action == "execute":
            self._draw_secondary_text(
                f"Remote execute progress: {waiting_count} waiting | {running_count} running | "
                f"{finished_count} finished | {error_count} issue(s)."
            )
        elif self.multibox_active_action == "preview" and (finished_count > 0 or error_count > 0):
            self._draw_secondary_text(
                f"Last remote preview batch: {finished_count} finished | {error_count} issue(s)."
            )
        elif self.multibox_active_action == "execute" and (finished_count > 0 or error_count > 0):
            self._draw_secondary_text(
                f"Last remote execute batch: {finished_count} finished | {error_count} issue(s)."
            )
        elif no_selection:
            self._draw_secondary_text("Select one or more active follower accounts to use Merchant Rules multibox actions.")
        self._draw_secondary_text("Followers must have Merchant Rules enabled and loaded to answer remote preview or execute requests.")

        if sync_clicked:
            self._start_multibox_sync()
        if preview_clicked:
            self._start_multibox_batch("preview", MERCHANT_RULES_OPCODE_PREVIEW)
        if execute_clicked:
            self._start_multibox_batch("execute", MERCHANT_RULES_OPCODE_EXECUTE)

    def _draw_guided_empty_state(self):
        self._draw_section_heading("Quick Start")
        PyImGui.text_wrapped("No merchant rules are set up yet. Add the first rule you want this widget to manage.")
        PyImGui.spacing()
        self._draw_section_heading("Buy")
        if PyImGui.button("Merchant Stock##guided_buy_stock"):
            self._add_buy_rule_of_kind(BUY_KIND_MERCHANT_STOCK)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Crafting Materials##guided_buy_materials"):
            self._add_buy_rule_of_kind(BUY_KIND_MATERIAL_TARGET)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Runes & Insignias##guided_buy_runes"):
            self._add_buy_rule_of_kind(BUY_KIND_RUNE_TRADER_TARGET)
            return
        PyImGui.spacing()
        self._draw_section_heading("Sell")
        if PyImGui.button("Specific Items##guided_sell_specific"):
            self._add_sell_rule_of_kind(SELL_KIND_EXPLICIT_MODELS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Materials##guided_sell_common"):
            self._add_sell_rule_of_kind(SELL_KIND_COMMON_MATERIALS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Weapons##guided_sell_weapons"):
            self._add_sell_rule_of_kind(SELL_KIND_WEAPONS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Armor##guided_sell_armor"):
            self._add_sell_rule_of_kind(SELL_KIND_ARMOR)
            return
        PyImGui.spacing()
        self._draw_section_heading("Destroy")
        if PyImGui.button("Specific Items##guided_destroy_specific"):
            self._add_destroy_rule_of_kind(DESTROY_KIND_EXPLICIT_MODELS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Materials##guided_destroy_materials"):
            self._add_destroy_rule_of_kind(DESTROY_KIND_MATERIALS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Weapons##guided_destroy_weapons"):
            self._add_destroy_rule_of_kind(DESTROY_KIND_WEAPONS)
            return
        PyImGui.same_line(0, 8)
        if PyImGui.button("Armor##guided_destroy_armor"):
            self._add_destroy_rule_of_kind(DESTROY_KIND_ARMOR)
            return
        PyImGui.spacing()
        self._draw_section_heading("Cleanup")
        if PyImGui.button("Open Cleanup Workspace##guided_open_cleanup"):
            self._set_active_rules_workspace(RULES_WORKSPACE_CLEANUP)
            return

    def _draw_status_section(self):
        supported_map, supported_reason, coords = self._get_supported_context(passive=True)
        current_map_id = int(Map.GetMapID() or 0)
        current_map_name = Map.GetMapName(current_map_id) if current_map_id > 0 else "Unknown"
        support_label, support_color = self._get_support_state(supported_map, coords)
        preview_label, preview_color, preview_detail = self._get_preview_state()
        actionable_entries, skipped_entries = self._split_preview_entries(self.preview_plan.entries)
        direct_count, conditional_count, skipped_count = self._get_preview_entry_counts(self.preview_plan.entries)
        inventory_plus = get_widget_handler().get_widget_info("Inventory Plus")

        self._draw_section_heading("Status")
        PyImGui.text(f"Map: {current_map_name} ({current_map_id})")
        PyImGui.same_line(0, 8)
        self._draw_inline_badge(support_label, support_color)
        self._draw_secondary_text(supported_reason)

        PyImGui.text("Preview:")
        PyImGui.same_line(0, 8)
        self._draw_inline_badge(preview_label, preview_color)
        if self.preview_ready and (actionable_entries or skipped_entries):
            PyImGui.same_line(0, 8)
            self._draw_secondary_text(
                f"{direct_count} direct | {conditional_count} conditional | {skipped_count} skipped",
                wrapped=False,
            )
        self._draw_secondary_text(preview_detail)
        if self.preview_ready and self._plan_needs_exact_storage_scan(self.preview_plan):
            exact_scan_message = (
                "Storage-aware planning is still partial. Use Open Xunlai for exact storage scan to confirm exact withdraws and make Xunlai steps direct before Execute."
                if self._can_use_local_storage_actions()
                else "Storage-aware planning is still partial. Exact Xunlai counts will stay estimated until Execute reaches an outpost or Guild Hall and can open storage."
            )
            PyImGui.text_colored(exact_scan_message, UI_COLOR_WARNING)
        elif self.preview_ready and str(self.preview_plan.storage_plan_state) == STORAGE_PLAN_STATE_EXACT_READY:
            self._draw_secondary_text("Xunlai is open, so storage-aware planning is using exact inventory + storage counts where needed.")
        elif self.preview_ready and self._plan_has_conditional_cleanup_actions(self.preview_plan):
            self._draw_secondary_text("Planned Xunlai cleanup steps are conditional until storage can be opened during Execute.")
        if self.preview_ready and not supported_map and self._plan_has_local_destroy_actions(self.preview_plan) and self._plan_has_local_storage_actions(self.preview_plan):
            PyImGui.text_colored("Merchant NPC support is unavailable here, but local destroy actions and Xunlai cleanup work can still execute.", UI_COLOR_WARNING)
        elif self.preview_ready and not supported_map and self._plan_has_local_destroy_actions(self.preview_plan):
            PyImGui.text_colored("Local destroy actions are still executable here even though merchant NPC support is unavailable.", UI_COLOR_WARNING)
        elif self.preview_ready and not supported_map and self._plan_has_local_storage_actions(self.preview_plan):
            PyImGui.text_colored("Merchant NPC support is unavailable here, but Xunlai cleanup work can still execute.", UI_COLOR_WARNING)
        if self.execute_drift_requires_confirmation and self.preview_inventory_diff_summary:
            PyImGui.text_colored(self.preview_inventory_diff_summary, UI_COLOR_WARNING)

        cleanup_state_label = "On" if self.auto_cleanup_on_outpost_entry else "Off"
        cleanup_state_color = UI_COLOR_SUCCESS if self.auto_cleanup_on_outpost_entry else UI_COLOR_MUTED
        PyImGui.text("Cleanup:")
        PyImGui.same_line(0, 8)
        self._draw_inline_badge(cleanup_state_label, cleanup_state_color)
        PyImGui.same_line(0, 8)
        self._draw_secondary_text(
            f"{len(_normalize_cleanup_targets(self.cleanup_targets))} explicit target(s) | "
            f"{len(_normalize_cleanup_protection_sources(self.cleanup_protection_sources))} linked source(s)",
            wrapped=False,
        )
        if self.auto_cleanup_running:
            PyImGui.text_colored("Cleanup / Xunlai is running.", UI_COLOR_INFO)

        PyImGui.text("NPCs:")
        PyImGui.same_line(0, 8)
        npc_badges = (
            ("Merchant", coords[MERCHANT_TYPE_MERCHANT] is not None),
            ("Materials", coords[MERCHANT_TYPE_MATERIALS] is not None),
            ("Rune Trader", coords[MERCHANT_TYPE_RUNE_TRADER] is not None),
            ("Rare Trader", coords[MERCHANT_TYPE_RARE_MATERIALS] is not None),
        )
        for badge_index, (label, available) in enumerate(npc_badges):
            self._draw_inline_badge(label, UI_COLOR_SUCCESS if available else UI_COLOR_MUTED)
            if badge_index + 1 < len(npc_badges):
                PyImGui.same_line(0, 6)

        if not self._has_any_rules():
            self._draw_secondary_text("No merchant rules are configured yet.", wrapped=False)
            PyImGui.same_line(0, 8)
            if PyImGui.small_button("Open Rules##merchant_rules_open_rules"):
                self._set_active_workspace(WORKSPACE_RULES)

        if inventory_plus and inventory_plus.enabled:
            PyImGui.text_colored("Inventory Plus will pause while merchant actions run.", UI_COLOR_WARNING)
        if self.destroy_instant_enabled:
            PyImGui.text_colored("Instant Destroy is active for this session.", UI_COLOR_DANGER)
        if self.destroy_include_protected_items:
            PyImGui.text_colored("Include Protected Items is active for this session.", UI_COLOR_DANGER)
        if self.last_instant_destroy_summary:
            self._draw_secondary_text(self.last_instant_destroy_summary)
        if self.last_cleanup_summary:
            self._draw_secondary_text(self.last_cleanup_summary)
        if self.profile_warning:
            PyImGui.text_colored(f"Live Config: {self.profile_warning}", UI_COLOR_WARNING)
        elif self.profile_notice:
            self._draw_secondary_text(f"Live Config: {self.profile_notice}")
        if self.last_error:
            PyImGui.text_colored(f"Last error: {self.last_error}", UI_COLOR_DANGER)
        elif self.last_execution_summary:
            self._draw_secondary_text(self.last_execution_summary)

        if (
            self.status_message
            and self.status_message != "Preview the current map plan before execution."
            and self.status_message not in {
                self.last_instant_destroy_summary,
                self.last_cleanup_summary,
                self.last_execution_summary,
            }
        ):
            self._draw_secondary_text(self.status_message)

        if PyImGui.collapsing_header("Catalog & Debug##merchant_rules_catalog_debug"):
            debug_logging = PyImGui.checkbox("Debug Logging##merchant_rules_debug_logging", bool(self.debug_logging))
            if debug_logging != self.debug_logging:
                self.debug_logging = debug_logging
                self._save_profile()
                if self.debug_logging:
                    self._log_catalog_summary("Debug logging enabled")
            PyImGui.same_line(0, 8)
            if PyImGui.small_button("Reload Catalog##merchant_rules_reload_catalog"):
                self._reload_catalog()
            self._draw_secondary_text(self._get_catalog_summary_text())
            if self.catalog_load_error:
                PyImGui.text_colored(self.catalog_load_error, UI_COLOR_WARNING)
            PyImGui.separator()
            self._draw_section_heading("Runtime Diagnostics")
            self._draw_runtime_diagnostics_section()

    def _draw_travel_summary(self):
        self._draw_section_heading("Travel")
        if not self.auto_travel_enabled:
            self._draw_secondary_text("Auto Travel is off.")
        else:
            target_label = self._format_outpost_label(self.target_outpost_id) if self.target_outpost_id > 0 else "Target not selected"
            target_color = UI_COLOR_INFO if self.target_outpost_id > 0 else UI_COLOR_WARNING
            PyImGui.text("Target:")
            PyImGui.same_line(0, 8)
            PyImGui.text_colored(target_label, target_color)
            if self.target_outpost_id > 0:
                self._draw_secondary_text(self._get_outpost_selector_guidance(self.target_outpost_id))
            else:
                self._draw_secondary_text("Auto-travel stays idle until you choose an outpost. Preview uses the current live context until then.")

        if PyImGui.collapsing_header("Travel Settings##merchant_rules_travel_settings"):
            self._draw_travel_section()

    def _draw_travel_section(self):
        section_changed = False
        enabled = PyImGui.checkbox("Enable Auto Travel##travel_enabled", self.auto_travel_enabled)
        if enabled != self.auto_travel_enabled:
            self.auto_travel_enabled = enabled
            if self.auto_travel_enabled and self.target_outpost_id <= 0 and Map.IsOutpost():
                self.target_outpost_id = int(Map.GetMapID() or 0)
                self.outpost_search_text = ""
            section_changed = True

        current_map_id = int(Map.GetMapID() or 0)
        target_label = self._format_outpost_label(self.target_outpost_id) if self.target_outpost_id > 0 else "Target not selected"
        PyImGui.text_wrapped(f"Target Outpost: {target_label}")

        if self.auto_travel_enabled:
            if Map.IsOutpost():
                if PyImGui.small_button("Use Current Outpost##travel_current"):
                    self.target_outpost_id = current_map_id
                    self.outpost_search_text = ""
                    section_changed = True
                PyImGui.same_line(0, 8)

            if PyImGui.small_button("Clear Target##travel_clear"):
                self.target_outpost_id = 0
                self.outpost_search_text = ""
                section_changed = True

            updated_search_text = PyImGui.input_text("Search Outposts##travel_search", self.outpost_search_text)
            if updated_search_text != self.outpost_search_text:
                self.outpost_search_text = updated_search_text

            picked_outpost_id = self._draw_outpost_search_results("travel_search_results", self.outpost_search_text)
            if picked_outpost_id > 0 and picked_outpost_id != self.target_outpost_id:
                self.target_outpost_id = picked_outpost_id
                self.outpost_search_text = ""
                section_changed = True

            if self.target_outpost_id > 0:
                PyImGui.text_wrapped(self._get_outpost_selector_guidance(self.target_outpost_id))
                if self.target_outpost_id in self.favorite_outpost_ids:
                    if PyImGui.small_button("Remove Favorite##travel_favorite_remove"):
                        self.favorite_outpost_ids = [outpost_id for outpost_id in self.favorite_outpost_ids if outpost_id != self.target_outpost_id]
                        section_changed = True
                else:
                    if PyImGui.small_button("Add Favorite##travel_favorite_add"):
                        self.favorite_outpost_ids = self._normalize_outpost_ids(self.favorite_outpost_ids + [self.target_outpost_id])
                        section_changed = True

                if Map.IsMapIDMatch(current_map_id, self.target_outpost_id):
                    PyImGui.text_wrapped("You are already in the selected outpost, so preview will show the full merchant plan.")
                else:
                    PyImGui.text_wrapped("Preview projects the post-travel plan. Travel + Execute will travel there, rebuild live merchant handling, and then run it.")
            else:
                PyImGui.text_wrapped("No specific target selected. Auto-travel stays idle until you choose an outpost.")

            if self.favorite_outpost_ids:
                PyImGui.text("Favorites")
                favorite_height = min(140, 28 + (22 * len(self.favorite_outpost_ids)))
                if PyImGui.begin_child("travel_favorites", (0, favorite_height), True, PyImGui.WindowFlags.NoFlag):
                    for outpost_id in list(self.favorite_outpost_ids):
                        if PyImGui.small_button(f"Use##travel_favorite_use_{outpost_id}"):
                            self.target_outpost_id = outpost_id
                            self.outpost_search_text = ""
                            section_changed = True
                        PyImGui.same_line(0, 6)
                        if PyImGui.small_button(f"X##travel_favorite_delete_{outpost_id}"):
                            self.favorite_outpost_ids = [value for value in self.favorite_outpost_ids if value != outpost_id]
                            section_changed = True
                            break
                        PyImGui.same_line(0, 6)
                        PyImGui.text(self._format_outpost_label(outpost_id))
                PyImGui.end_child()

        if section_changed:
            self._save_profile()
            self._mark_preview_dirty("Travel settings changed. Preview again before execution.")

    def _draw_rule_header_row(
        self,
        table_id: str,
        tree_label: str,
        type_label: str,
        type_color: tuple[float, float, float, float],
        summary_text: str,
        state_label: str,
        state_color: tuple[float, float, float, float],
        checkbox_label: str,
        enabled: bool,
        *,
        force_open: bool = False,
    ) -> tuple[bool, bool, bool]:
        table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV
        if PyImGui.begin_table(table_id, 3, table_flags):
            PyImGui.table_setup_column("Rule", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Summary", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Enabled", PyImGui.TableColumnFlags.WidthFixed, 95.0)
            PyImGui.table_next_row()

            PyImGui.table_set_column_index(0)
            PyImGui.text_colored("|", type_color)
            PyImGui.same_line(0, 6)
            self._draw_inline_badge(type_label, type_color)
            PyImGui.same_line(0, 8)
            tree_flags = getattr(PyImGui.TreeNodeFlags, "SpanFullWidth", PyImGui.TreeNodeFlags.NoFlag)
            if force_open:
                self._debug_log(f"Protections jump applying rule-header force-open before tree node: {tree_label}")
                self._force_next_item_open(True)
            self._push_rule_header_hover_style()
            opened = PyImGui.tree_node_ex(tree_label, tree_flags)
            header_clicked = bool(PyImGui.is_item_clicked(0))
            PyImGui.pop_style_color(3)

            PyImGui.table_set_column_index(1)
            self._draw_inline_badge(state_label, state_color)
            if summary_text:
                PyImGui.same_line(0, 6)
                PyImGui.text_wrapped(summary_text)

            PyImGui.table_set_column_index(2)
            new_enabled = PyImGui.checkbox(checkbox_label, enabled)
            PyImGui.end_table()
            return bool(opened), bool(new_enabled), header_clicked

        PyImGui.text_colored("|", type_color)
        PyImGui.same_line(0, 6)
        self._draw_inline_badge(type_label, type_color)
        PyImGui.same_line(0, 8)
        if force_open:
            self._debug_log(f"Protections jump applying rule-header force-open before tree node: {tree_label}")
            self._force_next_item_open(True)
        self._push_rule_header_hover_style()
        opened = PyImGui.tree_node(tree_label)
        header_clicked = bool(PyImGui.is_item_clicked(0))
        PyImGui.pop_style_color(3)
        PyImGui.same_line(0, 8)
        self._draw_inline_badge(state_label, state_color)
        if summary_text:
            PyImGui.same_line(0, 6)
            PyImGui.text(summary_text)
        PyImGui.same_line(0, 8)
        new_enabled = PyImGui.checkbox(checkbox_label, enabled)
        return bool(opened), bool(new_enabled), header_clicked

    def _format_sell_protection_jump_target_debug(self, target: SellProtectionJumpTarget | None = None) -> str:
        active_target = target if target is not None else self.sell_protection_jump_target
        if active_target is None:
            return "none"
        return (
            f"rule_index={int(active_target.owner_rule_index)} "
            f"kind={str(active_target.owner_rule_kind)} "
            f"anchor={str(active_target.subsection_anchor or '-')} "
            f"target_key={str(active_target.target_key or '-')} "
            f"needs_advanced={bool(active_target.requires_advanced)} "
            f"force_rule_open={bool(active_target.force_rule_open)} "
            f"force_advanced_open={bool(active_target.force_advanced_open)} "
            f"pending_rule_scroll={bool(active_target.pending_rule_scroll)} "
            f"pending_outer_scroll={bool(active_target.pending_outer_scroll)} "
            f"pending_inner_scroll={bool(active_target.pending_inner_scroll)}"
        )

    def _force_next_item_open(self, is_open: bool):
        set_next_item_open = getattr(PyImGui, "set_next_item_open", None)
        if set_next_item_open is None:
            return
        cond = None
        imgui_cond = getattr(PyImGui, "ImGuiCond", None)
        if imgui_cond is not None:
            cond = getattr(imgui_cond, "Always", None)
        if cond is None:
            cond = getattr(PyImGui, "ImGuiCond_Always", None)
        try:
            if cond is not None:
                set_next_item_open(bool(is_open), int(cond))
            else:
                set_next_item_open(bool(is_open))
        except TypeError:
            set_next_item_open(bool(is_open))
        except Exception as exc:
            self._debug_log(f"Protections jump force-open fallback failed: {exc}")

    def _clear_sell_protection_jump(self, reason: str = ""):
        if self.sell_protection_jump_target is not None and reason:
            self._debug_log(
                f"Protections jump cleared: {reason} | {self._format_sell_protection_jump_target_debug()}"
            )
        self.sell_protection_jump_target = None

    def _set_active_workspace(self, workspace_id: str, *, preserve_sell_protection_jump: bool = False):
        next_workspace = str(workspace_id or WORKSPACE_OVERVIEW)
        if next_workspace == self.active_workspace:
            return
        self.active_workspace = next_workspace
        if not preserve_sell_protection_jump:
            self._clear_sell_protection_jump(f"workspace changed to {next_workspace}")

    def _set_active_rules_workspace(self, workspace_id: str, *, preserve_sell_protection_jump: bool = False):
        next_workspace = str(workspace_id or RULES_WORKSPACE_BUY)
        if next_workspace == self.active_rules_workspace:
            return
        self.active_rules_workspace = next_workspace
        if not preserve_sell_protection_jump:
            self._clear_sell_protection_jump(f"rules workspace changed to {next_workspace}")

    def _set_active_sell_rule_kind(self, rule_kind: str, *, preserve_sell_protection_jump: bool = False):
        next_kind = str(rule_kind or SELL_RULE_WORKSPACE_ORDER[0])
        if next_kind == self.active_sell_rule_kind:
            return
        self.active_sell_rule_kind = next_kind
        if not preserve_sell_protection_jump:
            self._clear_sell_protection_jump(f"sell subsection changed to {next_kind}")

    def _get_sell_protection_jump_target(self) -> SellProtectionJumpTarget | None:
        target = self.sell_protection_jump_target
        if target is None or int(target.owner_rule_index) < 0:
            return None
        return target

    def _is_sell_jump_target_anchor(self, index: int, subsection_anchor: str) -> bool:
        target = self._get_sell_protection_jump_target()
        return bool(
            target is not None
            and int(target.owner_rule_index) == int(index)
            and str(target.subsection_anchor) == str(subsection_anchor)
        )

    def _maybe_scroll_sell_jump_target_row(self, index: int, subsection_anchor: str, target_key: str):
        target = self._get_sell_protection_jump_target()
        if target is None or not bool(target.pending_inner_scroll):
            return
        if int(target.owner_rule_index) != int(index) or str(target.subsection_anchor) != str(subsection_anchor):
            return
        if not str(target.target_key or "") or str(target.target_key) != str(target_key or ""):
            return
        PyImGui.set_scroll_here_y(0.25)
        target.pending_inner_scroll = False

    def _begin_sell_jump_target_group(self, index: int, subsection_anchor: str, label: str) -> bool:
        is_target = self._is_sell_jump_target_anchor(index, subsection_anchor)
        PyImGui.begin_group()
        if is_target:
            PyImGui.text_colored(label, UI_COLOR_INFO)
            PyImGui.same_line(0, 8)
            self._draw_inline_badge("Jump Target", UI_COLOR_INFO)
            target = self._get_sell_protection_jump_target()
            if target is not None and bool(target.pending_outer_scroll):
                PyImGui.set_scroll_here_y(0.22)
                target.pending_outer_scroll = False
        else:
            PyImGui.text(label)
        return is_target

    def _end_sell_jump_target_group(self, index: int, subsection_anchor: str):
        PyImGui.end_group()
        if not self._is_sell_jump_target_anchor(index, subsection_anchor):
            return

        rect_min_x, rect_min_y = PyImGui.get_item_rect_min()
        rect_max_x, rect_max_y = PyImGui.get_item_rect_max()
        pad_x = 6.0
        pad_y = 4.0
        fill_color = _color_tuple_to_imgui_u32(UI_COLOR_INFO, alpha_scale=0.10)
        border_color = _color_tuple_to_imgui_u32(UI_COLOR_INFO, alpha_scale=0.75)
        accent_color = _color_tuple_to_imgui_u32(UI_COLOR_INFO, alpha_scale=0.95)
        PyImGui.draw_list_add_rect_filled(
            rect_min_x - pad_x,
            rect_min_y - pad_y,
            rect_max_x + pad_x,
            rect_max_y + pad_y,
            fill_color,
            4.0,
            0,
        )
        PyImGui.draw_list_add_rect(
            rect_min_x - pad_x,
            rect_min_y - pad_y,
            rect_max_x + pad_x,
            rect_max_y + pad_y,
            border_color,
            4.0,
            0,
            1.5,
        )
        PyImGui.draw_list_add_rect_filled(
            rect_min_x - pad_x,
            rect_min_y - pad_y,
            rect_min_x - pad_x + 3.0,
            rect_max_y + pad_y,
            accent_color,
            2.0,
            0,
        )

        target = self._get_sell_protection_jump_target()
        if target is None:
            return
        if bool(target.ignore_interaction_until_mouse_release):
            if not (
                PyImGui.is_mouse_down(0)
                or PyImGui.is_mouse_down(1)
                or PyImGui.is_mouse_down(2)
                or PyImGui.is_mouse_clicked(0)
                or PyImGui.is_mouse_clicked(1)
                or PyImGui.is_mouse_clicked(2)
            ):
                target.ignore_interaction_until_mouse_release = False
            return

        if PyImGui.is_item_hovered() and (PyImGui.is_mouse_clicked(0) or PyImGui.is_mouse_clicked(1)):
            self._clear_sell_protection_jump("interacted inside highlighted subsection")

    def _request_jump_to_sell_rule(
        self,
        index: int,
        rule_kind: str,
        *,
        subsection_anchor: str = "",
        target_key: str = "",
        requires_advanced: bool = False,
    ):
        if index < 0:
            return
        if self.sell_protection_jump_target is not None:
            self._clear_sell_protection_jump("replaced by another jump request")
        self._set_active_workspace(WORKSPACE_RULES, preserve_sell_protection_jump=True)
        self._set_active_rules_workspace(RULES_WORKSPACE_SELL, preserve_sell_protection_jump=True)
        if rule_kind in SELL_RULE_WORKSPACE_ORDER:
            self._set_active_sell_rule_kind(rule_kind, preserve_sell_protection_jump=True)
        self.sell_protection_jump_target = SellProtectionJumpTarget(
            owner_rule_index=int(index),
            owner_rule_kind=str(rule_kind),
            subsection_anchor=str(subsection_anchor or ""),
            target_key=str(target_key or ""),
            requires_advanced=bool(requires_advanced),
            force_rule_open=True,
            force_advanced_open=bool(requires_advanced),
            pending_rule_scroll=True,
            pending_outer_scroll=True,
            pending_inner_scroll=bool(target_key),
            ignore_interaction_until_mouse_release=True,
        )
        self._debug_log(
            "Protections jump created: "
            + self._format_sell_protection_jump_target_debug(self.sell_protection_jump_target)
        )

    def _get_default_sell_rule_protection_jump_target(self, rule: SellRule) -> tuple[str, str]:
        normalized_rule = _normalize_sell_rule(rule)
        if normalized_rule is None or normalized_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
            return "", ""

        if normalized_rule.blacklist_model_ids:
            first_model_id = int(normalized_rule.blacklist_model_ids[0])
            return SELL_PROTECTION_ANCHOR_MODELS, f"model:{first_model_id}"

        if normalized_rule.kind == SELL_KIND_WEAPONS:
            if normalized_rule.blacklist_item_type_ids:
                first_item_type_id = int(normalized_rule.blacklist_item_type_ids[0])
                return SELL_PROTECTION_ANCHOR_WEAPON_TYPES, f"item_type:{first_item_type_id}"
            if normalized_rule.protected_weapon_requirement_rules:
                for first_requirement_rule in normalized_rule.protected_weapon_requirement_rules:
                    if not _is_weapon_requirement_range_active(
                        getattr(first_requirement_rule, "min_requirement", 0),
                        getattr(first_requirement_rule, "max_requirement", 0),
                    ):
                        continue
                    return (
                        SELL_PROTECTION_ANCHOR_REQUIREMENTS,
                        f"requirement_model:{int(first_requirement_rule.model_id)}",
                    )
            if _is_weapon_requirement_range_active(
                getattr(normalized_rule, "all_weapons_min_requirement", 0),
                getattr(normalized_rule, "all_weapons_max_requirement", 0),
            ):
                return SELL_PROTECTION_ANCHOR_REQUIREMENTS, SELL_PROTECTION_TARGET_KEY_ALL_WEAPONS_REQUIREMENT
            if normalized_rule.protected_weapon_mod_identifiers:
                first_identifier = str(normalized_rule.protected_weapon_mod_identifiers[0])
                return SELL_PROTECTION_ANCHOR_WEAPON_MODS, f"identifier:{first_identifier}"
            return "", ""

        if normalized_rule.protected_rune_identifiers:
            first_identifier = str(normalized_rule.protected_rune_identifiers[0])
            return SELL_PROTECTION_ANCHOR_RUNES, f"identifier:{first_identifier}"
        return "", ""

    def _build_protection_hub_entries(self) -> list[ProtectionHubEntry]:
        entries: list[ProtectionHubEntry] = []
        for index, raw_rule in enumerate(self.sell_rules):
            normalized_rule = _normalize_sell_rule(raw_rule)
            if normalized_rule is None or normalized_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                continue

            owner_kind_label = SELL_RULE_WORKSPACE_LABELS.get(
                normalized_rule.kind,
                SELL_KIND_LABELS.get(normalized_rule.kind, "Sell"),
            )
            owner_rule_label = self._format_sell_rule_reference(index, normalized_rule)
            owner_rule_order = self._get_sell_rule_order_within_kind(index, normalized_rule.kind)
            owner_enabled = bool(normalized_rule.enabled)

            def append_entry(
                filter_key: str,
                protection_type_label: str,
                value_label: str,
                value_sort_key: str = "",
                *,
                subsection_anchor: str,
                target_key: str = "",
                requires_advanced: bool = True,
            ):
                safe_value = str(value_label or "").strip()
                if not safe_value:
                    return
                search_text = " ".join(
                    part.lower()
                    for part in (
                        "sell rule",
                        protection_type_label,
                        safe_value,
                        owner_rule_label,
                        owner_kind_label,
                        str(owner_rule_order),
                    )
                    if str(part or "").strip()
                )
                entries.append(
                    ProtectionHubEntry(
                        source_label="Sell Rule",
                        filter_key=filter_key,
                        protection_type_label=protection_type_label,
                        value_label=safe_value,
                        value_sort_key=str(value_sort_key or safe_value).lower(),
                        owner_rule_index=int(index),
                        owner_rule_kind=str(normalized_rule.kind),
                        owner_rule_kind_label=owner_kind_label,
                        owner_rule_label=owner_rule_label,
                        owner_rule_enabled=owner_enabled,
                        owner_rule_order=owner_rule_order,
                        search_text=search_text,
                        subsection_anchor=str(subsection_anchor),
                        target_key=str(target_key or ""),
                        requires_advanced=bool(requires_advanced),
                    )
                )

            for model_id in normalized_rule.blacklist_model_ids:
                append_entry(
                    PROTECTION_FILTER_MODELS,
                    "Protected Model",
                    self._format_model_label(model_id),
                    f"{int(model_id):09d}",
                    subsection_anchor=SELL_PROTECTION_ANCHOR_MODELS,
                    target_key=f"model:{int(model_id)}",
                )

            if normalized_rule.kind == SELL_KIND_WEAPONS:
                for item_type_id in normalized_rule.blacklist_item_type_ids:
                    append_entry(
                        PROTECTION_FILTER_WEAPON_TYPES,
                        "Protected Weapon Type",
                        self._get_weapon_item_type_label(item_type_id),
                        f"{int(item_type_id):04d}",
                        subsection_anchor=SELL_PROTECTION_ANCHOR_WEAPON_TYPES,
                        target_key=f"item_type:{int(item_type_id)}",
                    )

                all_weapons_min_requirement, all_weapons_max_requirement = _normalize_weapon_requirement_range(
                    getattr(normalized_rule, "all_weapons_min_requirement", 0),
                    getattr(normalized_rule, "all_weapons_max_requirement", 0),
                )
                if _is_weapon_requirement_range_active(all_weapons_min_requirement, all_weapons_max_requirement):
                    append_entry(
                        PROTECTION_FILTER_REQUIREMENTS,
                        "Req Range",
                        f"All weapons req {all_weapons_min_requirement}-{all_weapons_max_requirement}",
                        f"global-{all_weapons_min_requirement:02d}-{all_weapons_max_requirement:02d}",
                        subsection_anchor=SELL_PROTECTION_ANCHOR_REQUIREMENTS,
                        target_key=SELL_PROTECTION_TARGET_KEY_ALL_WEAPONS_REQUIREMENT,
                    )

                for requirement_rule in normalized_rule.protected_weapon_requirement_rules:
                    min_requirement, max_requirement = _normalize_weapon_requirement_range(
                        getattr(requirement_rule, "min_requirement", 0),
                        getattr(requirement_rule, "max_requirement", 0),
                    )
                    if not _is_weapon_requirement_range_active(min_requirement, max_requirement):
                        continue
                    append_entry(
                        PROTECTION_FILTER_REQUIREMENTS,
                        "Req Range",
                        f"{self._format_model_label(requirement_rule.model_id)} req {min_requirement}-{max_requirement}",
                        f"{int(requirement_rule.model_id):09d}-{min_requirement:02d}-{max_requirement:02d}",
                        subsection_anchor=SELL_PROTECTION_ANCHOR_REQUIREMENTS,
                        target_key=f"requirement_model:{int(requirement_rule.model_id)}",
                    )

                for identifier in normalized_rule.protected_weapon_mod_identifiers:
                    append_entry(
                        PROTECTION_FILTER_WEAPON_MODS,
                        "Protected Weapon Mod",
                        self._get_weapon_mod_label(identifier),
                        str(identifier),
                        subsection_anchor=SELL_PROTECTION_ANCHOR_WEAPON_MODS,
                        target_key=f"identifier:{str(identifier)}",
                    )
            else:
                for identifier in normalized_rule.protected_rune_identifiers:
                    append_entry(
                        PROTECTION_FILTER_RUNES,
                        "Protected Rune / Insignia",
                        self._get_rune_label(identifier),
                        str(identifier),
                        subsection_anchor=SELL_PROTECTION_ANCHOR_RUNES,
                        target_key=f"identifier:{str(identifier)}",
                    )

        filter_sort_order = {
            PROTECTION_FILTER_MODELS: 0,
            PROTECTION_FILTER_WEAPON_TYPES: 1,
            PROTECTION_FILTER_REQUIREMENTS: 2,
            PROTECTION_FILTER_WEAPON_MODS: 3,
            PROTECTION_FILTER_RUNES: 4,
        }
        entries.sort(
            key=lambda entry: (
                SELL_RULE_WORKSPACE_ORDER.index(entry.owner_rule_kind) if entry.owner_rule_kind in SELL_RULE_WORKSPACE_ORDER else 99,
                int(entry.owner_rule_order),
                filter_sort_order.get(entry.filter_key, 99),
                entry.value_sort_key,
            )
        )
        return entries

    def _entry_matches_protection_filters(self, entry: ProtectionHubEntry) -> bool:
        if self.protections_active_only and not bool(entry.owner_rule_enabled):
            return False
        if self.protections_owner_filter != PROTECTION_FILTER_ALL and entry.owner_rule_kind != self.protections_owner_filter:
            return False
        if self.protections_type_filter != PROTECTION_FILTER_ALL and entry.filter_key != self.protections_type_filter:
            return False

        query = str(self.protections_search_text or "").strip().lower()
        if not query:
            return True
        return all(token in entry.search_text for token in query.split())

    def _draw_protections_section(self):
        entries = self._build_protection_hub_entries()
        filtered_entries = [entry for entry in entries if self._entry_matches_protection_filters(entry)]
        owner_rule_indices = {entry.owner_rule_index for entry in entries}
        enabled_owner_rule_indices = {entry.owner_rule_index for entry in entries if entry.owner_rule_enabled}
        type_counts = {
            filter_key: sum(1 for entry in entries if entry.filter_key == filter_key)
            for filter_key, _label in PROTECTION_TYPE_FILTER_OPTIONS
            if filter_key != PROTECTION_FILTER_ALL
        }

        self._draw_section_heading("Protections")
        PyImGui.text_colored(
            "Protections currently aggregates protection entries owned by Sell rules. It is a central hub, not a separate protection engine yet.",
            UI_COLOR_INFO,
        )
        self._draw_secondary_text(
            "Destroy consults these protections by default. Use Jump to Rule to edit the owning sell rule; entries here are read-mostly for now."
        )
        if self.destroy_include_protected_items:
            PyImGui.text_colored(
                "Include Protected Items is active for this session, so Destroy may still include protected items in Preview, Execute, and Instant Destroy.",
                UI_COLOR_DANGER,
            )

        PyImGui.separator()
        self._draw_section_heading("Summary")
        self._draw_secondary_text(
            (
                f"{len(entries)} protection entr{'y' if len(entries) == 1 else 'ies'} across {len(owner_rule_indices)} sell rule(s). "
                f"{len(enabled_owner_rule_indices)} owner rule(s) enabled, {max(0, len(owner_rule_indices) - len(enabled_owner_rule_indices))} disabled."
            ),
            wrapped=False,
        )
        summary_parts = [
            f"{label}: {int(type_counts.get(filter_key, 0))}"
            for filter_key, label in PROTECTION_TYPE_FILTER_OPTIONS
            if filter_key != PROTECTION_FILTER_ALL
        ]
        self._draw_secondary_text(" | ".join(summary_parts), wrapped=False)

        PyImGui.spacing()
        updated_search_text = PyImGui.input_text("Search Protections##merchant_rules_protections_search", self.protections_search_text)
        if updated_search_text != self.protections_search_text:
            self.protections_search_text = updated_search_text

        active_only = PyImGui.checkbox("Active Only##merchant_rules_protections_active_only", bool(self.protections_active_only))
        if active_only != self.protections_active_only:
            self.protections_active_only = active_only

        owner_filter_labels = [label for _key, label in PROTECTION_OWNER_FILTER_OPTIONS]
        owner_filter_keys = [key for key, _label in PROTECTION_OWNER_FILTER_OPTIONS]
        current_owner_filter_index = owner_filter_keys.index(self.protections_owner_filter) if self.protections_owner_filter in owner_filter_keys else 0
        next_owner_filter_index = PyImGui.combo("Owner Scope##merchant_rules_protections_owner_filter", current_owner_filter_index, owner_filter_labels)
        if 0 <= next_owner_filter_index < len(owner_filter_keys):
            self.protections_owner_filter = owner_filter_keys[next_owner_filter_index]

        type_filter_labels = [label for _key, label in PROTECTION_TYPE_FILTER_OPTIONS]
        type_filter_keys = [key for key, _label in PROTECTION_TYPE_FILTER_OPTIONS]
        current_type_filter_index = type_filter_keys.index(self.protections_type_filter) if self.protections_type_filter in type_filter_keys else 0
        next_type_filter_index = PyImGui.combo("Type##merchant_rules_protections_type_filter", current_type_filter_index, type_filter_labels)
        if 0 <= next_type_filter_index < len(type_filter_keys):
            self.protections_type_filter = type_filter_keys[next_type_filter_index]

        PyImGui.spacing()
        if not entries:
            self._draw_secondary_text("No protection entries are configured yet. Add protections to weapon or armor sell rules and they will appear here.")
            return
        if not filtered_entries:
            self._draw_secondary_text("No protection entries match the current search and filters.")
            return

        if PyImGui.begin_child("merchant_rules_protections_table_child", (0, 0), True, PyImGui.WindowFlags.NoFlag):
            table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV
            if PyImGui.begin_table("merchant_rules_protections_table", 8, table_flags):
                PyImGui.table_setup_column("Source", PyImGui.TableColumnFlags.WidthFixed, 85.0)
                PyImGui.table_setup_column("Type", PyImGui.TableColumnFlags.WidthFixed, 140.0)
                PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Owner Kind", PyImGui.TableColumnFlags.WidthFixed, 90.0)
                PyImGui.table_setup_column("Owner Rule", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Enabled", PyImGui.TableColumnFlags.WidthFixed, 72.0)
                PyImGui.table_setup_column("Order", PyImGui.TableColumnFlags.WidthFixed, 58.0)
                PyImGui.table_setup_column("Jump", PyImGui.TableColumnFlags.WidthFixed, 58.0)

                PyImGui.table_next_row()
                for column_index, column_label in enumerate(("Source", "Type", "Value", "Owner Kind", "Owner Rule", "Enabled", "Order", "Jump")):
                    PyImGui.table_set_column_index(column_index)
                    self._draw_secondary_text(column_label, wrapped=False)

                for row_index, entry in enumerate(filtered_entries):
                    PyImGui.table_next_row()

                    PyImGui.table_set_column_index(0)
                    PyImGui.text(entry.source_label)

                    PyImGui.table_set_column_index(1)
                    PyImGui.text(entry.protection_type_label)

                    PyImGui.table_set_column_index(2)
                    PyImGui.text(entry.value_label)

                    PyImGui.table_set_column_index(3)
                    self._draw_inline_badge(entry.owner_rule_kind_label, RULE_KIND_PRESENTATION.get(entry.owner_rule_kind, ("Rule", UI_COLOR_SUBTLE))[1])

                    PyImGui.table_set_column_index(4)
                    PyImGui.text(entry.owner_rule_label)

                    PyImGui.table_set_column_index(5)
                    enabled_label = "Yes" if entry.owner_rule_enabled else "No"
                    enabled_color = UI_COLOR_SUCCESS if entry.owner_rule_enabled else UI_COLOR_MUTED
                    PyImGui.text_colored(enabled_label, enabled_color)

                    PyImGui.table_set_column_index(6)
                    PyImGui.text(str(int(entry.owner_rule_order)))

                    PyImGui.table_set_column_index(7)
                    if PyImGui.small_button(f"Go##merchant_rules_protection_jump_{row_index}_{entry.owner_rule_index}"):
                        self._request_jump_to_sell_rule(
                            entry.owner_rule_index,
                            entry.owner_rule_kind,
                            subsection_anchor=entry.subsection_anchor,
                            target_key=entry.target_key,
                            requires_advanced=entry.requires_advanced,
                        )

                PyImGui.end_table()
        PyImGui.end_child()

    def _draw_buy_rule_merchant_stock_editor(self, index: int, rule: BuyRule) -> bool:
        changed = False
        self._draw_secondary_text(f"Merchant: {MERCHANT_TYPE_LABELS[_get_buy_rule_merchant_type(rule)]}", wrapped=False)
        merchant_stock_targets = _normalize_merchant_stock_targets(rule.merchant_stock_targets)

        if PyImGui.button(f"Clear Items##buy_stock_clear_{index}"):
            if self._set_buy_rule_merchant_stock_targets(rule, []):
                merchant_stock_targets = []
                changed = True

        PyImGui.text(f"Selected Items: {len(merchant_stock_targets)}")
        if not merchant_stock_targets:
            self._draw_secondary_text("No merchant stock items selected yet.", wrapped=False)
            return changed

        updated_targets = [
            MerchantStockTarget(
                model_id=merchant_stock_target.model_id,
                target_count=merchant_stock_target.target_count,
                max_per_run=merchant_stock_target.max_per_run,
            )
            for merchant_stock_target in merchant_stock_targets
        ]
        display_targets = self._sort_targets_by_model_label_for_display(updated_targets)
        removed_model_id = 0
        child_height = min(220, 58 + (32 * len(updated_targets)))
        if PyImGui.begin_child(f"buy_merchant_stock_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table(f"buy_merchant_stock_selected_table_{index}", 4, PyImGui.TableFlags.NoFlag):
                PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthFixed, 130.0)
                PyImGui.table_setup_column("Max/Run", PyImGui.TableColumnFlags.WidthFixed, 130.0)
                PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Item")
                PyImGui.table_set_column_index(1)
                PyImGui.text("Target")
                PyImGui.table_set_column_index(2)
                PyImGui.text("Max/Run")
                PyImGui.table_set_column_index(3)
                PyImGui.text("Remove")

                for target_row in display_targets:
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(self._format_model_label_short(target_row.model_id))

                    PyImGui.table_set_column_index(1)
                    PyImGui.push_item_width(120)
                    new_target_count = PyImGui.input_int(
                        f"##buy_stock_target_count_{index}_{target_row.model_id}",
                        int(target_row.target_count),
                    )
                    PyImGui.pop_item_width()
                    target_row.target_count = max(0, int(new_target_count))

                    PyImGui.table_set_column_index(2)
                    PyImGui.push_item_width(120)
                    new_max_per_run = PyImGui.input_int(
                        f"##buy_stock_max_per_run_{index}_{target_row.model_id}",
                        int(target_row.max_per_run),
                    )
                    PyImGui.pop_item_width()
                    target_row.max_per_run = max(0, int(new_max_per_run))

                    PyImGui.table_set_column_index(3)
                    if PyImGui.small_button(f"X##buy_stock_remove_{index}_{target_row.model_id}"):
                        removed_model_id = target_row.model_id
                        break

                PyImGui.end_table()
        PyImGui.end_child()

        if removed_model_id > 0:
            next_targets = [
                target
                for target in updated_targets
                if int(target.model_id) != int(removed_model_id)
            ]
            if self._set_buy_rule_merchant_stock_targets(rule, next_targets):
                changed = True
        elif self._set_buy_rule_merchant_stock_targets(rule, updated_targets):
            changed = True

        return changed

    def _draw_buy_rule_material_targets_editor(self, index: int, rule: BuyRule) -> bool:
        changed = False
        material_targets = _normalize_material_targets(rule.material_targets)

        if PyImGui.button(f"Clear Materials##buy_material_clear_{index}"):
            if self._set_buy_rule_material_targets(rule, []):
                material_targets = []
                changed = True

        PyImGui.text(f"Selected Materials: {len(material_targets)}")
        if not material_targets:
            PyImGui.text_wrapped("No crafting materials selected yet.")
            return changed

        updated_targets = [
            MaterialTarget(
                model_id=material_target.model_id,
                target_count=material_target.target_count,
                max_per_run=material_target.max_per_run,
            )
            for material_target in material_targets
        ]
        display_targets = self._sort_targets_by_model_label_for_display(updated_targets)
        removed_model_id = 0
        child_height = min(220, 58 + (32 * len(updated_targets)))
        if PyImGui.begin_child(f"buy_material_targets_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_table(f"buy_material_targets_table_{index}", 5, PyImGui.TableFlags.NoFlag):
                PyImGui.table_setup_column("Material", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Trader", PyImGui.TableColumnFlags.WidthFixed, 115.0)
                PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthFixed, 130.0)
                PyImGui.table_setup_column("Max/Run", PyImGui.TableColumnFlags.WidthFixed, 130.0)
                PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Material")
                PyImGui.table_set_column_index(1)
                PyImGui.text("Trader")
                PyImGui.table_set_column_index(2)
                PyImGui.text("Target")
                PyImGui.table_set_column_index(3)
                PyImGui.text("Max/Run")
                PyImGui.table_set_column_index(4)
                PyImGui.text("Remove")

                for target_row in display_targets:
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(self._format_model_label_short(target_row.model_id))

                    PyImGui.table_set_column_index(1)
                    PyImGui.text(MERCHANT_TYPE_LABELS[self._get_material_merchant_type_by_model(target_row.model_id)])

                    PyImGui.table_set_column_index(2)
                    PyImGui.push_item_width(120)
                    new_target_count = PyImGui.input_int(
                        f"##buy_material_target_count_{index}_{target_row.model_id}",
                        int(target_row.target_count),
                    )
                    PyImGui.pop_item_width()
                    target_row.target_count = max(0, int(new_target_count))

                    PyImGui.table_set_column_index(3)
                    PyImGui.push_item_width(120)
                    new_max_per_run = PyImGui.input_int(
                        f"##buy_material_max_per_run_{index}_{target_row.model_id}",
                        int(target_row.max_per_run),
                    )
                    PyImGui.pop_item_width()
                    target_row.max_per_run = max(0, int(new_max_per_run))

                    PyImGui.table_set_column_index(4)
                    if PyImGui.small_button(f"X##buy_material_remove_{index}_{target_row.model_id}"):
                        removed_model_id = target_row.model_id
                        break

                PyImGui.end_table()
        PyImGui.end_child()

        if removed_model_id > 0:
            next_targets = [target for target in updated_targets if target.model_id != removed_model_id]
            if self._set_buy_rule_material_targets(rule, next_targets):
                changed = True
        elif self._set_buy_rule_material_targets(rule, updated_targets):
            changed = True

        return changed

    def _draw_buy_rule_rune_targets_editor(self, index: int, rule: BuyRule) -> bool:
        changed = False
        rune_targets = _normalize_rune_trader_targets(rule.rune_targets)

        if PyImGui.button(f"Clear Targets##buy_runes_clear_{index}"):
            if self._set_buy_rule_rune_targets(rule, []):
                rune_targets = []
                changed = True

        PyImGui.text(f"Selected Targets: {len(rune_targets)}")
        if not rune_targets:
            self._draw_secondary_text("No rune or insignia targets selected yet.", wrapped=False)
        else:
            updated_targets = [
                RuneTraderTarget(
                    identifier=target.identifier,
                    target_count=target.target_count,
                    max_per_run=target.max_per_run,
                )
                for target in rune_targets
            ]
            display_targets = self._sort_targets_by_identifier_label_for_display(updated_targets, self._get_rune_label)
            removed_identifier = ""
            child_height = min(240, 58 + (32 * len(updated_targets)))
            if PyImGui.begin_child(f"buy_rune_targets_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.begin_table(f"buy_rune_targets_table_{index}", 5, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("Rune / Insignia", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Type", PyImGui.TableColumnFlags.WidthFixed, 110.0)
                    PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthFixed, 120.0)
                    PyImGui.table_setup_column("Max/Run", PyImGui.TableColumnFlags.WidthFixed, 120.0)
                    PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Rune / Insignia")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Type")
                    PyImGui.table_set_column_index(2)
                    PyImGui.text("Target")
                    PyImGui.table_set_column_index(3)
                    PyImGui.text("Max/Run")
                    PyImGui.table_set_column_index(4)
                    PyImGui.text("Remove")

                    for target_row in display_targets:
                        entry = self._get_rune_buy_entry(target_row.identifier) or {}
                        kind_label = str(entry.get("kind_label", "") or "Rune / Insignia")

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(self._get_rune_label(target_row.identifier))

                        PyImGui.table_set_column_index(1)
                        PyImGui.text(kind_label)

                        PyImGui.table_set_column_index(2)
                        PyImGui.push_item_width(110)
                        new_target_count = PyImGui.input_int(
                            f"##buy_rune_target_count_{index}_{target_row.identifier}",
                            int(target_row.target_count),
                        )
                        PyImGui.pop_item_width()
                        target_row.target_count = max(0, int(new_target_count))

                        PyImGui.table_set_column_index(3)
                        PyImGui.push_item_width(110)
                        new_max_per_run = PyImGui.input_int(
                            f"##buy_rune_max_per_run_{index}_{target_row.identifier}",
                            int(target_row.max_per_run),
                        )
                        PyImGui.pop_item_width()
                        target_row.max_per_run = max(0, int(new_max_per_run))

                        PyImGui.table_set_column_index(4)
                        if PyImGui.small_button(f"X##buy_rune_remove_{index}_{target_row.identifier}"):
                            removed_identifier = target_row.identifier
                            break

                    PyImGui.end_table()
            PyImGui.end_child()

            if removed_identifier:
                next_targets = [
                    target
                    for target in updated_targets
                    if target.identifier != removed_identifier
                ]
                if self._set_buy_rule_rune_targets(rule, next_targets):
                    changed = True
            elif self._set_buy_rule_rune_targets(rule, updated_targets):
                changed = True

        if not self.rune_buy_professions:
            self._draw_secondary_text("Rune catalog entries are unavailable, so only saved targets can be edited right now.")
            return changed

        active_profession = str(self.buy_rune_profession_cache.get(index, self.rune_buy_professions[0]) or self.rune_buy_professions[0])
        if active_profession not in self.rune_buy_professions:
            active_profession = self.rune_buy_professions[0]

        for tab_index, profession in enumerate(self.rune_buy_professions):
            profession_label = _get_rune_profession_label(profession)
            button_label = (
                f"{profession_label} ({len(self.rune_buy_entries_by_profession.get(profession, []))})"
                f"##buy_rune_profession_{index}_{profession}"
            )
            if self._draw_workspace_button(
                button_label,
                active=active_profession == profession,
                color=UI_COLOR_PURPLE_ACCENT,
            ):
                active_profession = profession
            if tab_index + 1 < len(self.rune_buy_professions):
                PyImGui.same_line(0, 6)
        self.buy_rune_profession_cache[index] = active_profession

        search_text = self.buy_rune_search_cache.get(index, "")
        updated_search_text = PyImGui.input_text(f"Search Runes / Insignias##buy_rune_search_{index}", search_text)
        if updated_search_text != search_text:
            self.buy_rune_search_cache[index] = updated_search_text

        existing_identifiers = {
            _normalize_rune_identifier(target.identifier)
            for target in _normalize_rune_trader_targets(rule.rune_targets)
            if _normalize_rune_identifier(target.identifier)
        }
        query = str(self.buy_rune_search_cache.get(index, "") or "").strip().lower()
        visible_entries: list[dict[str, object]] = []
        for entry in self.rune_buy_entries_by_profession.get(active_profession, []):
            identifier = str(entry.get("identifier", "") or "").strip()
            name = str(entry.get("name", "") or "").strip()
            kind_label = str(entry.get("kind_label", "") or "").strip()
            rarity = str(entry.get("rarity", "") or "").strip()
            if query and query not in identifier.lower() and query not in name.lower() and query not in kind_label.lower() and query not in rarity.lower():
                continue
            visible_entries.append(entry)

        addable_identifiers = [
            str(entry.get("identifier", "")).strip()
            for entry in visible_entries
            if str(entry.get("identifier", "")).strip() not in existing_identifiers
        ]
        if self._draw_add_all_matches_button(
            f"buy_rune_results_add_all_{index}",
            len(visible_entries),
            len(addable_identifiers),
        ):
            added_any = False
            for identifier in addable_identifiers:
                if self._add_buy_rule_rune_target(rule, identifier):
                    added_any = True
            if added_any:
                changed = True

        child_height = 220 if len(visible_entries) > 6 else 170
        if PyImGui.begin_child(f"buy_rune_results_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
            if not visible_entries:
                PyImGui.text_wrapped("No matching runes or insignias found in this profession tab.")
            elif PyImGui.begin_table(f"buy_rune_results_table_{index}", 4, PyImGui.TableFlags.RowBg):
                PyImGui.table_setup_column("Rune / Insignia", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Type", PyImGui.TableColumnFlags.WidthFixed, 105.0)
                PyImGui.table_setup_column("Rarity", PyImGui.TableColumnFlags.WidthFixed, 85.0)
                PyImGui.table_setup_column("Add", PyImGui.TableColumnFlags.WidthFixed, 55.0)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Rune / Insignia")
                PyImGui.table_set_column_index(1)
                PyImGui.text("Type")
                PyImGui.table_set_column_index(2)
                PyImGui.text("Rarity")
                PyImGui.table_set_column_index(3)
                PyImGui.text("Add")

                for entry in visible_entries:
                    identifier = str(entry.get("identifier", "") or "").strip()
                    if not identifier:
                        continue
                    already_selected = identifier in existing_identifiers

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(str(entry.get("name", "") or identifier))

                    PyImGui.table_set_column_index(1)
                    PyImGui.text(str(entry.get("kind_label", "") or "Rune / Insignia"))

                    PyImGui.table_set_column_index(2)
                    PyImGui.text(str(entry.get("rarity", "") or "-"))

                    PyImGui.table_set_column_index(3)
                    PyImGui.begin_disabled(already_selected)
                    add_clicked = PyImGui.small_button(f"+##buy_rune_add_{index}_{identifier}")
                    PyImGui.end_disabled()
                    if add_clicked and self._add_buy_rule_rune_target(rule, identifier):
                        changed = True
                        self.buy_rune_search_cache[index] = str(entry.get("name", "") or identifier)

                PyImGui.end_table()
        PyImGui.end_child()
        return changed

    def _draw_buy_rule_editor(self, index: int, rule: BuyRule) -> bool:
        changed = False
        summary_text, ready = self._get_buy_rule_summary(rule)
        state_label, state_color = self._get_rule_state_badge(enabled=bool(rule.enabled), ready=ready)
        type_label, type_color = self._get_rule_type_presentation(rule.kind)

        opened, enabled, _header_clicked = self._draw_rule_header_row(
            f"buy_rule_header_{index}",
            f"{self._get_rule_display_label(rule, BUY_KIND_LABELS.get(rule.kind, 'Buy Rule'))}###buy_rule_{index}",
            type_label,
            type_color,
            summary_text,
            state_label,
            state_color,
            f"Enabled##buy_enabled_{index}",
            bool(rule.enabled),
        )
        if enabled != rule.enabled:
            rule.enabled = enabled
            changed = True

        if not opened:
            return changed

        self._draw_section_heading("Basic")
        self._draw_secondary_text(
            f"Category: {BUY_RULE_WORKSPACE_LABELS.get(rule.kind, BUY_KIND_LABELS.get(rule.kind, 'Buy Rule'))}",
            wrapped=False,
        )
        updated_rule_name = self._draw_rule_name_input(f"Rule Name (Optional)##buy_rule_name_{index}", rule.name)
        if updated_rule_name != rule.name:
            rule.name = updated_rule_name
            changed = True

        if rule.kind == BUY_KIND_MERCHANT_STOCK:
            changed = self._draw_buy_rule_merchant_stock_editor(index, rule) or changed
            existing_stock_target_ids = {
                max(0, _safe_int(merchant_stock_target.model_id, 0))
                for merchant_stock_target in _normalize_merchant_stock_targets(rule.merchant_stock_targets)
            }

            if self.catalog_merchant_essentials:
                PyImGui.text("Quick Picks")
                for quick_index, entry in enumerate(self.catalog_merchant_essentials):
                    if PyImGui.small_button(f"{entry['name']}##buy_quick_{index}_{entry['model_id']}"):
                        default_target = max(0, _safe_int(entry.get("default_target", 0), 0))
                        if self._add_buy_rule_merchant_stock_target(
                            rule,
                            int(entry["model_id"]),
                            target_count=default_target,
                        ):
                            changed = True
                        self.buy_model_search_cache[index] = str(entry["name"])
                    if quick_index % 2 == 0 and quick_index + 1 < len(self.catalog_merchant_essentials):
                        PyImGui.same_line(0, 6)

            search_text = self.buy_model_search_cache.get(index, "")
            updated_search_text = PyImGui.input_text(f"Search Items##buy_search_{index}", search_text)
            if updated_search_text != search_text:
                self.buy_model_search_cache[index] = updated_search_text

            picked_model_id, visible_buy_model_ids = self._draw_search_results(
                f"buy_search_results_{index}",
                self.buy_model_search_cache.get(index, ""),
            )
            addable_buy_model_ids = [model_id for model_id in visible_buy_model_ids if model_id not in existing_stock_target_ids]
            if self._draw_add_all_matches_button(
                f"buy_search_results_add_all_{index}",
                len(visible_buy_model_ids),
                len(addable_buy_model_ids),
            ):
                added_any = False
                for model_id in addable_buy_model_ids:
                    if self._add_buy_rule_merchant_stock_target(rule, model_id):
                        added_any = True
                if added_any:
                    changed = True
            if picked_model_id > 0:
                if self._add_buy_rule_merchant_stock_target(rule, picked_model_id):
                    changed = True
                self.buy_model_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)

            if PyImGui.collapsing_header(f"Advanced##buy_advanced_{index}"):
                manual_model_id = max(0, int(self.buy_manual_model_id_cache.get(index, 0)))
                updated_manual_model_id = PyImGui.input_int(f"Manual Model ID##buy_model_{index}", manual_model_id)
                updated_manual_model_id = max(0, int(updated_manual_model_id))
                if updated_manual_model_id != manual_model_id:
                    self.buy_manual_model_id_cache[index] = updated_manual_model_id
                PyImGui.same_line(0, 8)
                PyImGui.begin_disabled(updated_manual_model_id <= 0)
                add_manual_item = PyImGui.small_button(f"Add Item##buy_add_manual_model_{index}")
                PyImGui.end_disabled()
                if add_manual_item and self._add_buy_rule_merchant_stock_target(rule, updated_manual_model_id):
                    changed = True
                    self.buy_manual_model_id_cache[index] = 0
                    self.buy_model_search_cache[index] = self._get_model_name(updated_manual_model_id) or str(updated_manual_model_id)
        elif rule.kind == BUY_KIND_MATERIAL_TARGET:
            self._draw_secondary_text("Common materials buy in lots of 10. Rare materials buy in singles.")
            changed = self._draw_buy_rule_material_targets_editor(index, rule) or changed

            common_entries = self._get_common_material_catalog_entries()
            rare_entries = self._get_rare_material_catalog_entries()

            if common_entries:
                PyImGui.text("Quick Picks - Common Materials")
                for quick_index, entry in enumerate(common_entries):
                    if PyImGui.small_button(f"{entry['name']}##buy_common_material_{index}_{entry['model_id']}"):
                        if self._add_buy_rule_material_target(rule, int(entry["model_id"])):
                            changed = True
                        self.buy_model_search_cache[index] = str(entry["name"])
                    if quick_index % 2 == 0 and quick_index + 1 < len(common_entries):
                        PyImGui.same_line(0, 6)

            if rare_entries:
                PyImGui.text("Quick Picks - Rare Materials")
                for quick_index, entry in enumerate(rare_entries):
                    if PyImGui.small_button(f"{entry['name']}##buy_rare_material_{index}_{entry['model_id']}"):
                        if self._add_buy_rule_material_target(rule, int(entry["model_id"])):
                            changed = True
                        self.buy_model_search_cache[index] = str(entry["name"])
                    if quick_index % 2 == 0 and quick_index + 1 < len(rare_entries):
                        PyImGui.same_line(0, 6)

            search_text = self.buy_model_search_cache.get(index, "")
            updated_search_text = PyImGui.input_text(f"Search Materials##buy_material_search_{index}", search_text)
            if updated_search_text != search_text:
                self.buy_model_search_cache[index] = updated_search_text

            picked_model_id, visible_material_model_ids = self._draw_material_search_results(
                f"buy_material_results_{index}",
                self.buy_model_search_cache.get(index, ""),
            )
            existing_material_target_ids = {
                max(0, _safe_int(material_target.model_id, 0))
                for material_target in _normalize_material_targets(rule.material_targets)
            }
            addable_material_model_ids = [model_id for model_id in visible_material_model_ids if model_id not in existing_material_target_ids]
            if self._draw_add_all_matches_button(
                f"buy_material_results_add_all_{index}",
                len(visible_material_model_ids),
                len(addable_material_model_ids),
            ):
                added_any = False
                for model_id in addable_material_model_ids:
                    if self._add_buy_rule_material_target(rule, model_id):
                        added_any = True
                if added_any:
                    changed = True
            if picked_model_id > 0:
                if self._add_buy_rule_material_target(rule, picked_model_id):
                    changed = True
                self.buy_model_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)
        elif rule.kind == BUY_KIND_RUNE_TRADER_TARGET:
            self._draw_secondary_text("Maintains exact standalone runes and insignias. Inventory is topped up from storage first, then from the Rune Trader.")
            self._draw_secondary_text("Preview stays passive by default. Use Open Xunlai for exact storage scan when you want exact storage-aware planning.")
            changed = self._draw_buy_rule_rune_targets_editor(index, rule) or changed

        PyImGui.spacing()
        same_kind_indices = self._get_buy_rule_indices_for_kind(rule.kind)
        same_kind_position = same_kind_indices.index(index) if index in same_kind_indices else -1
        move_up_target_index = same_kind_indices[same_kind_position - 1] if same_kind_position > 0 else -1
        move_down_target_index = same_kind_indices[same_kind_position + 1] if 0 <= same_kind_position < len(same_kind_indices) - 1 else -1

        PyImGui.begin_disabled(move_up_target_index < 0)
        move_up = PyImGui.small_button(f"Move Up##buy_move_up_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(move_down_target_index < 0)
        move_down = PyImGui.small_button(f"Move Down##buy_move_down_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        if PyImGui.button(f"Remove Rule##buy_remove_{index}"):
            self.buy_rules.pop(index)
            self.rule_ui_structure_changed = True
            self._refresh_rule_ui_caches()
            changed = True
            PyImGui.tree_pop()
            return changed
        if move_up:
            if self._move_rule_entry(self.buy_rules, index, move_up_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed
        if move_down:
            if self._move_rule_entry(self.buy_rules, index, move_down_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed

        PyImGui.tree_pop()
        return changed

    def _draw_sell_rule_rarity_toggles(self, index: int, rule: SellRule) -> bool:
        changed = False
        PyImGui.text("Rarity Filters")
        rarity_options = _get_rarity_options_for_rule(rule.kind)
        for rarity_index, (rarity_key, rarity_label) in enumerate(rarity_options):
            current_value = bool(rule.rarities.get(rarity_key, False))
            new_value = PyImGui.checkbox(f"##sell_rarity_{index}_{rarity_key}", current_value)
            if new_value != current_value:
                rule.rarities[rarity_key] = new_value
                changed = True
            PyImGui.same_line(0, 4)
            PyImGui.text_colored(rarity_label, RARITY_TEXT_COLORS.get(rarity_key, UI_COLOR_SUBTLE))
            if rarity_index % 2 == 0 and rarity_index + 1 < len(rarity_options):
                PyImGui.same_line(0, 12)
        return changed

    def _draw_sell_rule_blacklist_editor(self, index: int, rule: SellRule) -> bool:
        changed = False
        self._begin_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_MODELS, "Never Sell These Models")
        if PyImGui.button(f"Clear Protected Models##sell_blacklist_clear_{index}"):
            if self._set_sell_rule_blacklist_model_ids(rule, []):
                changed = True
            self.sell_blacklist_import_feedback_cache[index] = ("Cleared all protected models.", UI_COLOR_MUTED)
        PyImGui.same_line(0, 8)
        if PyImGui.button(f"Import From Clipboard##sell_blacklist_import_{index}"):
            try:
                clipboard_text = str(PyImGui.get_clipboard_text() or "")
            except Exception as exc:
                self.sell_blacklist_import_feedback_cache[index] = (f"Clipboard read failed: {exc}", UI_COLOR_DANGER)
            else:
                if not clipboard_text.strip():
                    self.sell_blacklist_import_feedback_cache[index] = ("Clipboard is empty.", UI_COLOR_WARNING)
                else:
                    parsed_batch_ids, invalid_count = _parse_batch_model_ids(clipboard_text)
                    if not parsed_batch_ids:
                        self.sell_blacklist_import_feedback_cache[index] = ("No valid model IDs found in clipboard.", UI_COLOR_WARNING)
                    else:
                        previous_count = len(rule.blacklist_model_ids)
                        merged_model_ids = rule.blacklist_model_ids + parsed_batch_ids
                        self._set_sell_rule_blacklist_model_ids(rule, merged_model_ids)
                        new_count = max(0, len(rule.blacklist_model_ids) - previous_count)
                        already_present_count = max(0, len(parsed_batch_ids) - new_count)
                        feedback_parts: list[str] = [f"Imported {new_count} model ID(s)."]
                        if already_present_count > 0:
                            feedback_parts.append(f"{already_present_count} already protected.")
                        if invalid_count > 0:
                            feedback_parts.append(f"Ignored {invalid_count} invalid token(s).")
                        feedback_color = UI_COLOR_SUCCESS if new_count > 0 else UI_COLOR_WARNING
                        self.sell_blacklist_import_feedback_cache[index] = (" ".join(feedback_parts), feedback_color)
                        if new_count > 0:
                            changed = True

        PyImGui.text(f"Protected Models: {len(rule.blacklist_model_ids)}")
        removed_model_id = self._draw_selected_model_ids(
            "sell_blacklist_models",
            index,
            rule.blacklist_model_ids,
            jump_anchor=SELL_PROTECTION_ANCHOR_MODELS,
        )
        if removed_model_id > 0:
            if self._set_sell_rule_blacklist_model_ids(
                rule,
                [model_id for model_id in rule.blacklist_model_ids if model_id != removed_model_id],
            ):
                changed = True

        feedback_message, feedback_color = self.sell_blacklist_import_feedback_cache.get(index, ("", UI_COLOR_MUTED))
        if feedback_message:
            PyImGui.text_colored(feedback_message, feedback_color)
        self._draw_secondary_text("Import from clipboard expects model IDs only, not runtime item-instance IDs.")

        entry_predicate: Callable[[dict[str, object]], bool] | None = None
        if rule.kind == SELL_KIND_WEAPONS:
            entry_predicate = self._catalog_entry_matches_weapon_blacklist
        elif rule.kind == SELL_KIND_ARMOR:
            include_standalone_runes = bool(rule.include_standalone_runes)
            entry_predicate = lambda entry: self._catalog_entry_matches_armor_blacklist(
                entry,
                include_standalone_runes=include_standalone_runes,
            )

        search_text = self.sell_blacklist_search_cache.get(index, "")
        updated_search_text = PyImGui.input_text(f"Protect Models By Name##sell_blacklist_search_{index}", search_text)
        if updated_search_text != search_text:
            self.sell_blacklist_search_cache[index] = updated_search_text

        picked_model_id, picked_group_info, search_debug, visible_item_model_ids = self._draw_blacklist_search_results(
            f"sell_blacklist_results_{index}",
            self.sell_blacklist_search_cache.get(index, ""),
            rule.blacklist_model_ids,
            entry_predicate=entry_predicate,
        )
        addable_blacklist_model_ids = [model_id for model_id in visible_item_model_ids if model_id not in rule.blacklist_model_ids]
        if self._draw_add_all_matches_button(
            f"sell_blacklist_results_add_all_{index}",
            len(visible_item_model_ids),
            len(addable_blacklist_model_ids),
        ):
            if self._set_sell_rule_blacklist_model_ids(rule, rule.blacklist_model_ids + addable_blacklist_model_ids):
                changed = True
        if self.debug_logging and search_debug.get("query"):
            PyImGui.text_wrapped(
                f"Debug: query='{search_debug.get('query', '')}' | "
                f"item matches={int(search_debug.get('item_results', 0) or 0)} | "
                f"alias groups={int(search_debug.get('alias_groups', 0) or 0)}"
            )
            if int(search_debug.get("item_results", 0) or 0) <= 0 and int(search_debug.get("alias_groups", 0) or 0) <= 0:
                if bool(search_debug.get("catalog_empty", False)):
                    PyImGui.text_wrapped("Debug: catalog is empty, so blacklist search cannot return results.")
                else:
                    PyImGui.text_wrapped("Debug: catalog loaded, but this query has no current matches.")

        if picked_group_info is not None:
            picked_group_model_ids = _dedupe_model_ids(list(picked_group_info.get("model_ids", [])))
            if self._set_sell_rule_blacklist_model_ids(rule, rule.blacklist_model_ids + picked_group_model_ids):
                changed = True
                display_name = str(picked_group_info.get("display_name", "")).strip() or "Matching Variants"
                self._debug_log(f"Blacklist add-all selected: {display_name} -> added {len(picked_group_model_ids)} model(s).")
                self.sell_blacklist_search_cache[index] = display_name
        elif picked_model_id > 0:
            if self._set_sell_rule_blacklist_model_ids(rule, rule.blacklist_model_ids + [picked_model_id]):
                changed = True
                self._debug_log(
                    f"Blacklist single model selected: {self._format_model_label(picked_model_id)}."
                )
            self.sell_blacklist_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)
        self._end_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_MODELS)
        return changed

    def _draw_sell_rule_weapon_type_blacklist_editor(self, index: int, rule: SellRule) -> bool:
        if rule.kind != SELL_KIND_WEAPONS:
            return False

        changed = False
        self._begin_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_WEAPON_TYPES, "Never Sell These Weapon Types")
        if PyImGui.button(f"Clear Weapon Type Protection##sell_weapon_type_blacklist_clear_{index}"):
            if self._set_sell_rule_blacklist_item_type_ids(rule, []):
                changed = True

        PyImGui.text(f"Protected Weapon Types: {len(rule.blacklist_item_type_ids)}")
        if rule.blacklist_item_type_ids:
            selected_labels = [self._get_weapon_item_type_label(item_type_id) for item_type_id in rule.blacklist_item_type_ids]
            PyImGui.text_wrapped(", ".join(selected_labels))
        else:
            PyImGui.text_wrapped("No weapon types selected yet.")

        for option_index, (item_type, label) in enumerate(WEAPON_ITEM_TYPE_OPTIONS):
            item_type_id = int(item_type.value)
            is_selected = item_type_id in rule.blacklist_item_type_ids
            new_selected = PyImGui.checkbox(
                f"{label}##sell_weapon_type_blacklist_{index}_{item_type_id}",
                is_selected,
            )
            self._maybe_scroll_sell_jump_target_row(index, SELL_PROTECTION_ANCHOR_WEAPON_TYPES, f"item_type:{int(item_type_id)}")
            if new_selected != is_selected:
                if new_selected:
                    new_ids = rule.blacklist_item_type_ids + [item_type_id]
                else:
                    new_ids = [value for value in rule.blacklist_item_type_ids if value != item_type_id]
                if self._set_sell_rule_blacklist_item_type_ids(rule, new_ids):
                    changed = True
            if (option_index + 1) % 3 != 0 and option_index + 1 < len(WEAPON_ITEM_TYPE_OPTIONS):
                PyImGui.same_line(0, 8)

        self._draw_secondary_text("Weapon-type protection is checked before requirement and weapon mod protection.")
        self._end_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_WEAPON_TYPES)
        return changed

    def _draw_sell_rule_weapon_requirement_editor(self, index: int, rule: SellRule) -> bool:
        if rule.kind != SELL_KIND_WEAPONS:
            return False

        changed = False
        normalized_all_weapons_min_requirement, normalized_all_weapons_max_requirement = _normalize_weapon_requirement_range(
            getattr(rule, "all_weapons_min_requirement", 0),
            getattr(rule, "all_weapons_max_requirement", 0),
        )
        if (
            normalized_all_weapons_min_requirement != getattr(rule, "all_weapons_min_requirement", 0)
            or normalized_all_weapons_max_requirement != getattr(rule, "all_weapons_max_requirement", 0)
        ):
            rule.all_weapons_min_requirement = normalized_all_weapons_min_requirement
            rule.all_weapons_max_requirement = normalized_all_weapons_max_requirement
            changed = True

        self._begin_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_REQUIREMENTS, "Protect All Weapons In Req Range")
        PyImGui.text("Low Req")
        PyImGui.same_line(0, 6)
        PyImGui.push_item_width(80)
        new_all_weapons_min_requirement = PyImGui.input_int(
            f"##sell_weapon_requirement_all_low_{index}",
            int(rule.all_weapons_min_requirement),
        )
        all_weapons_min_input_active = _get_last_imgui_item_active()
        PyImGui.pop_item_width()
        PyImGui.same_line(0, 12)
        PyImGui.text("High Req")
        PyImGui.same_line(0, 6)
        PyImGui.push_item_width(80)
        new_all_weapons_max_requirement = PyImGui.input_int(
            f"##sell_weapon_requirement_all_high_{index}",
            int(rule.all_weapons_max_requirement),
        )
        all_weapons_max_input_active = _get_last_imgui_item_active()
        PyImGui.pop_item_width()
        self._maybe_scroll_sell_jump_target_row(
            index,
            SELL_PROTECTION_ANCHOR_REQUIREMENTS,
            SELL_PROTECTION_TARGET_KEY_ALL_WEAPONS_REQUIREMENT,
        )
        all_weapons_input_active = all_weapons_min_input_active or all_weapons_max_input_active
        if not _should_defer_weapon_requirement_range_commit(
            new_all_weapons_min_requirement,
            new_all_weapons_max_requirement,
            input_active=all_weapons_input_active,
        ):
            normalized_all_weapons_min_requirement, normalized_all_weapons_max_requirement = _normalize_weapon_requirement_range(
                new_all_weapons_min_requirement,
                new_all_weapons_max_requirement,
            )
            if (
                normalized_all_weapons_min_requirement != rule.all_weapons_min_requirement
                or normalized_all_weapons_max_requirement != rule.all_weapons_max_requirement
            ):
                rule.all_weapons_min_requirement = normalized_all_weapons_min_requirement
                rule.all_weapons_max_requirement = normalized_all_weapons_max_requirement
                changed = True

        self._draw_secondary_text(
            f"Inclusive range. Set either endpoint to 0 to disable. Req 0 / unknown does not match range rules; "
            f"use unconditional model protection for unknown reqs. Values are capped at {MAX_WEAPON_REQUIREMENT}."
        )

        PyImGui.text("Never Sell These Models In Req Range")
        if PyImGui.button(f"Clear Model Requirement Protection##sell_weapon_requirement_clear_{index}"):
            if self._set_sell_rule_weapon_requirement_rules(rule, []):
                changed = True

        requirement_rules = list(rule.protected_weapon_requirement_rules)
        PyImGui.text(f"Protected Models: {len(requirement_rules)}")
        if requirement_rules:
            updated_rules = [
                WeaponRequirementRule(
                    model_id=requirement_rule.model_id,
                    min_requirement=requirement_rule.min_requirement,
                    max_requirement=requirement_rule.max_requirement,
                )
                for requirement_rule in requirement_rules
            ]
            display_rules = self._sort_targets_by_model_label_for_display(updated_rules)
            removed_model_id = 0
            child_height = min(220, 58 + (32 * len(updated_rules)))
            if PyImGui.begin_child(f"sell_weapon_requirement_selected_{index}", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.begin_table(f"sell_weapon_requirement_table_{index}", 4, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("Model", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Low Req", PyImGui.TableColumnFlags.WidthFixed, 100.0)
                    PyImGui.table_setup_column("High Req", PyImGui.TableColumnFlags.WidthFixed, 100.0)
                    PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Model")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Low Req")
                    PyImGui.table_set_column_index(2)
                    PyImGui.text("High Req")
                    PyImGui.table_set_column_index(3)
                    PyImGui.text("Remove")

                    for requirement_rule in display_rules:
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(self._format_model_label_short(requirement_rule.model_id))
                        self._maybe_scroll_sell_jump_target_row(
                            index,
                            SELL_PROTECTION_ANCHOR_REQUIREMENTS,
                            f"requirement_model:{int(requirement_rule.model_id)}",
                        )

                        PyImGui.table_set_column_index(1)
                        PyImGui.push_item_width(90)
                        new_min_requirement = PyImGui.input_int(
                            f"##sell_weapon_requirement_min_{index}_{requirement_rule.model_id}",
                            int(requirement_rule.min_requirement),
                        )
                        min_requirement_input_active = _get_last_imgui_item_active()
                        PyImGui.pop_item_width()

                        PyImGui.table_set_column_index(2)
                        PyImGui.push_item_width(90)
                        new_max_requirement = PyImGui.input_int(
                            f"##sell_weapon_requirement_max_{index}_{requirement_rule.model_id}",
                            int(requirement_rule.max_requirement),
                        )
                        max_requirement_input_active = _get_last_imgui_item_active()
                        PyImGui.pop_item_width()
                        requirement_input_active = min_requirement_input_active or max_requirement_input_active
                        if not _should_defer_weapon_requirement_range_commit(
                            new_min_requirement,
                            new_max_requirement,
                            input_active=requirement_input_active,
                        ):
                            (
                                requirement_rule.min_requirement,
                                requirement_rule.max_requirement,
                            ) = _normalize_weapon_requirement_range(new_min_requirement, new_max_requirement)

                        PyImGui.table_set_column_index(3)
                        if PyImGui.small_button(f"X##sell_weapon_requirement_remove_{index}_{requirement_rule.model_id}"):
                            removed_model_id = requirement_rule.model_id
                            break

                    PyImGui.end_table()
            PyImGui.end_child()

            if removed_model_id > 0:
                next_rules = [entry for entry in updated_rules if entry.model_id != removed_model_id]
                if self._set_sell_rule_weapon_requirement_rules(rule, next_rules):
                    changed = True
            elif self._set_sell_rule_weapon_requirement_rules(rule, updated_rules):
                changed = True
        else:
            self._draw_secondary_text("No requirement-protected weapon models selected yet.", wrapped=False)

        search_text = self.sell_weapon_requirement_search_cache.get(index, "")
        updated_search_text = PyImGui.input_text(f"Protect Weapon Models By Name##sell_weapon_requirement_search_{index}", search_text)
        if updated_search_text != search_text:
            self.sell_weapon_requirement_search_cache[index] = updated_search_text

        picked_model_id, _visible_model_ids = self._draw_weapon_search_results(
            f"sell_weapon_requirement_results_{index}",
            self.sell_weapon_requirement_search_cache.get(index, ""),
        )
        if picked_model_id > 0:
            default_min_requirement, default_max_requirement = _normalize_weapon_requirement_range(
                getattr(rule, "all_weapons_min_requirement", 0),
                getattr(rule, "all_weapons_max_requirement", 0),
            )
            if not _is_weapon_requirement_range_active(default_min_requirement, default_max_requirement):
                default_min_requirement, default_max_requirement = _normalize_weapon_requirement_range(1, 8)
            if self._add_sell_rule_weapon_requirement_rule(
                rule,
                picked_model_id,
                min_requirement=default_min_requirement,
                max_requirement=default_max_requirement,
            ):
                changed = True
            self.sell_weapon_requirement_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)

        self._draw_secondary_text(
            "Requirement ranges are inclusive and apply only to equippable weapons with a parsed req value. "
            "Valid per-model ranges decide that model before the all-weapons range is considered."
        )
        self._end_sell_jump_target_group(index, SELL_PROTECTION_ANCHOR_REQUIREMENTS)
        return changed

    def _draw_protected_identifier_editor(
        self,
        index: int,
        rule: SellRule,
        *,
        title: str,
        selected_identifiers: list[str],
        entries: list[dict[str, str]],
        formatter,
        setter,
        search_cache: dict[int, str],
        cache_suffix: str,
    ) -> bool:
        changed = False
        anchor = SELL_PROTECTION_ANCHOR_WEAPON_MODS if cache_suffix == "weapon_mods" else SELL_PROTECTION_ANCHOR_RUNES
        self._begin_sell_jump_target_group(index, anchor, title)
        if PyImGui.button(f"Clear {title}##sell_protected_clear_{cache_suffix}_{index}"):
            if setter(rule, []):
                changed = True

        PyImGui.text(f"Protected Entries: {len(selected_identifiers)}")
        removed_identifier = self._draw_selected_identifiers(
            f"sell_protected_{cache_suffix}",
            index,
            selected_identifiers,
            formatter,
            jump_anchor=anchor,
        )
        if removed_identifier:
            if setter(rule, [identifier for identifier in selected_identifiers if identifier != removed_identifier]):
                changed = True

        search_text = search_cache.get(index, "")
        updated_search_text = PyImGui.input_text(f"Protect By Name##sell_protected_search_{cache_suffix}_{index}", search_text)
        if updated_search_text != search_text:
            search_cache[index] = updated_search_text

        picked_identifier, visible_identifiers = self._draw_identifier_search_results(
            f"sell_protected_results_{cache_suffix}_{index}",
            search_cache.get(index, ""),
            entries,
        )
        addable_identifiers = [identifier for identifier in visible_identifiers if identifier not in selected_identifiers]
        if self._draw_add_all_matches_button(
            f"sell_protected_results_add_all_{cache_suffix}_{index}",
            len(visible_identifiers),
            len(addable_identifiers),
        ):
            if setter(rule, selected_identifiers + addable_identifiers):
                changed = True
        if picked_identifier:
            if setter(rule, selected_identifiers + [picked_identifier]):
                changed = True
            search_cache[index] = str(formatter(picked_identifier))
        self._end_sell_jump_target_group(index, anchor)
        return changed

    def _draw_sell_rule_editor(self, index: int, rule: SellRule) -> bool:
        changed = False
        jump_target = self._get_sell_protection_jump_target()
        is_target_rule = bool(jump_target is not None and int(jump_target.owner_rule_index) == int(index))
        highlight_basic_jump_target = bool(
            is_target_rule
            and jump_target is not None
            and not str(jump_target.subsection_anchor or "")
        )
        summary_text, ready = self._get_sell_rule_summary(rule)
        state_label, state_color = self._get_rule_state_badge(enabled=bool(rule.enabled), ready=ready)
        type_label, type_color = self._get_rule_type_presentation(rule.kind)

        if is_target_rule and bool(jump_target.force_rule_open):
            self._debug_log(
                f"Protections jump matching rule {int(index)}; preparing rule open | "
                f"{self._format_sell_protection_jump_target_debug(jump_target)}"
            )

        opened, enabled, header_clicked = self._draw_rule_header_row(
            f"sell_rule_header_{index}",
            f"{self._get_rule_display_label(rule, SELL_KIND_LABELS.get(rule.kind, 'Sell Rule'))}###sell_rule_{index}",
            type_label,
            type_color,
            summary_text,
            state_label,
            state_color,
            f"Enabled##sell_enabled_{index}",
            bool(rule.enabled),
            force_open=bool(is_target_rule and jump_target is not None and jump_target.force_rule_open),
        )
        if enabled != rule.enabled:
            rule.enabled = enabled
            changed = True
        if header_clicked and jump_target is not None and int(jump_target.owner_rule_index) != int(index):
            self._clear_sell_protection_jump(f"different rule clicked ({int(index)})")
            jump_target = None
            is_target_rule = False
        elif is_target_rule and jump_target is not None and bool(jump_target.pending_rule_scroll):
            PyImGui.set_scroll_here_y(0.25)
            jump_target.pending_rule_scroll = False
            jump_target.force_rule_open = False

        if not opened:
            if is_target_rule:
                self._clear_sell_protection_jump(f"target rule {int(index)} was not opened")
            return changed

        if highlight_basic_jump_target:
            self._begin_sell_jump_target_group(index, "", "Basic")
        else:
            self._draw_section_heading("Basic")
        self._draw_secondary_text(
            f"Category: {SELL_RULE_WORKSPACE_LABELS.get(rule.kind, SELL_KIND_LABELS.get(rule.kind, 'Sell Rule'))}",
            wrapped=False,
        )
        updated_rule_name = self._draw_rule_name_input(f"Rule Name (Optional)##sell_rule_name_{index}", rule.name)
        if updated_rule_name != rule.name:
            rule.name = updated_rule_name
            changed = True
        if highlight_basic_jump_target:
            self._end_sell_jump_target_group(index, "")

        normalized_rule = _normalize_sell_rule(rule)
        if normalized_rule is None:
            self._draw_secondary_text("This legacy sell rule type is no longer supported and will be removed on save.")
            return changed
        if rule.kind in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
            if rule.kind == SELL_KIND_WEAPONS:
                self._draw_secondary_text("Equippable weapons sell to Merchant. Standalone weapon mods route to the Rune Trader.")
            else:
                self._draw_secondary_text("Equippable armor sells to Merchant. Standalone runes and insignias are optional.")

            changed = self._draw_sell_rule_rarity_toggles(index, rule) or changed

            skip_customized = PyImGui.checkbox(f"Never Sell Customized Items##sell_skip_customized_{index}", bool(rule.skip_customized))
            if skip_customized != rule.skip_customized:
                rule.skip_customized = skip_customized
                changed = True

            PyImGui.same_line(0, 8)
            skip_unidentified = PyImGui.checkbox(f"Never Sell Unidentified Items##sell_skip_unidentified_{index}", bool(rule.skip_unidentified))
            if skip_unidentified != rule.skip_unidentified:
                rule.skip_unidentified = skip_unidentified
                changed = True

            if rule.kind == SELL_KIND_ARMOR:
                include_standalone_runes = PyImGui.checkbox(
                    f"Also Sell Standalone Runes / Insignias##sell_include_standalone_runes_{index}",
                    bool(rule.include_standalone_runes),
                )
                if include_standalone_runes != rule.include_standalone_runes:
                    rule.include_standalone_runes = include_standalone_runes
                    changed = True

            if is_target_rule and jump_target is not None and bool(jump_target.requires_advanced) and bool(jump_target.force_advanced_open):
                self._debug_log(
                    f"Protections jump forcing Advanced open for rule {int(index)} | "
                    f"{self._format_sell_protection_jump_target_debug(jump_target)}"
                )
                self._force_next_item_open(True)
            advanced_open = PyImGui.collapsing_header(f"Advanced##sell_advanced_{index}")
            if is_target_rule and jump_target is not None and bool(jump_target.requires_advanced):
                if advanced_open:
                    jump_target.force_advanced_open = False
                elif not bool(jump_target.force_advanced_open):
                    self._clear_sell_protection_jump(f"Advanced hidden for target rule {int(index)}")
                    jump_target = None
                    is_target_rule = False
            if advanced_open:
                changed = self._draw_sell_rule_blacklist_editor(index, rule) or changed
                if rule.kind == SELL_KIND_WEAPONS:
                    changed = self._draw_sell_rule_weapon_type_blacklist_editor(index, rule) or changed
                    changed = self._draw_sell_rule_weapon_requirement_editor(index, rule) or changed
                    changed = self._draw_protected_identifier_editor(
                        index,
                        rule,
                        title="Never Sell Items With These Weapon Mods",
                        selected_identifiers=rule.protected_weapon_mod_identifiers,
                        entries=self.weapon_mod_entries,
                        formatter=self._get_weapon_mod_label,
                        setter=self._set_sell_rule_weapon_mod_identifiers,
                        search_cache=self.sell_weapon_mod_search_cache,
                        cache_suffix="weapon_mods",
                    ) or changed
                else:
                    changed = self._draw_protected_identifier_editor(
                        index,
                        rule,
                        title="Never Sell Items With These Runes / Insignias",
                        selected_identifiers=rule.protected_rune_identifiers,
                        entries=self.rune_entries,
                        formatter=self._get_rune_label,
                        setter=self._set_sell_rule_rune_identifiers,
                        search_cache=self.sell_rune_search_cache,
                        cache_suffix="runes",
                    ) or changed
                    self._draw_secondary_text("Protection matches attached exact rune or insignia names, not the armor display name.")
        elif rule.kind == SELL_KIND_COMMON_MATERIALS:
            material_merchant_types = self._get_sell_material_merchant_types(rule.model_ids)
            merchant_labels = [
                MERCHANT_TYPE_LABELS.get(merchant_type, merchant_type)
                for merchant_type in material_merchant_types
            ]
            merchant_prefix = "Merchants" if len(material_merchant_types) > 1 else "Merchant"
            self._draw_secondary_text(f"{merchant_prefix}: {self._format_compact_list(merchant_labels, limit=2)}", wrapped=False)
            self._draw_secondary_text("Common materials sell in lots of 10. Rare materials sell individually.")
        else:
            self._draw_secondary_text(
                "Routing: standalone runes / insignias -> Rune Trader, common materials -> Material Trader with Merchant leftovers under 10, rare materials -> Rare Material Trader, everything else -> Merchant.",
            )

        if rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
            if rule.kind == SELL_KIND_COMMON_MATERIALS:
                if PyImGui.button(f"Add All Common Materials##sell_common_preset_{index}"):
                    if self._set_sell_rule_model_ids(index, rule, rule.model_ids + self._get_common_material_preset()):
                        changed = True
                PyImGui.same_line(0, 8)
                if PyImGui.button(f"Add All Rare Materials##sell_rare_preset_{index}"):
                    if self._set_sell_rule_model_ids(index, rule, rule.model_ids + self._get_rare_material_preset()):
                        changed = True
                if PyImGui.button(f"Replace With Common Materials##sell_common_replace_{index}"):
                    if self._set_sell_rule_model_ids(index, rule, self._get_common_material_preset()):
                        changed = True
                PyImGui.same_line(0, 8)
                if PyImGui.button(f"Replace With Rare Materials##sell_rare_replace_{index}"):
                    if self._set_sell_rule_model_ids(index, rule, self._get_rare_material_preset()):
                        changed = True
                self._draw_secondary_text("Search can mix common and rare crafting materials in one sell rule.")
            if PyImGui.button(f"Clear List##sell_clear_{index}"):
                if self._set_sell_rule_model_ids(index, rule, []):
                    changed = True

            whitelist_targets = _normalize_whitelist_targets(getattr(rule, "whitelist_targets", []))
            selected_label = "Selected Materials" if rule.kind == SELL_KIND_COMMON_MATERIALS else "Selected Items"
            item_column_label = "Material" if rule.kind == SELL_KIND_COMMON_MATERIALS else "Item"
            empty_text = "No crafting materials selected yet." if rule.kind == SELL_KIND_COMMON_MATERIALS else "No items selected yet."
            PyImGui.text(f"{selected_label}: {len(whitelist_targets)}")
            updated_targets, removed_model_id = self._draw_whitelist_targets(
                section_name="sell_models",
                index=index,
                targets=whitelist_targets,
                item_column_label=item_column_label,
                empty_text=empty_text,
                show_merchant_column=rule.kind == SELL_KIND_COMMON_MATERIALS,
                show_deposit_column=False,
                merchant_label_getter=lambda model_id: MERCHANT_TYPE_LABELS[self._get_material_merchant_type_by_model(model_id)],
            )
            if removed_model_id > 0:
                if self._set_sell_rule_model_ids(index, rule, [model_id for model_id in rule.model_ids if model_id != removed_model_id]):
                    changed = True
            elif self._set_sell_rule_whitelist_targets(index, rule, updated_targets):
                changed = True

            search_text = self.sell_model_search_cache.get(index, "")
            search_label = "Search Materials" if rule.kind == SELL_KIND_COMMON_MATERIALS else "Search Items"
            updated_search_text = PyImGui.input_text(f"{search_label}##sell_search_{index}", search_text)
            if updated_search_text != search_text:
                self.sell_model_search_cache[index] = updated_search_text

            if rule.kind == SELL_KIND_COMMON_MATERIALS:
                picked_model_id, visible_model_ids = self._draw_material_search_results(
                    f"sell_search_results_{index}",
                    self.sell_model_search_cache.get(index, ""),
                )
            else:
                picked_model_id, visible_model_ids = self._draw_search_results(
                    f"sell_search_results_{index}",
                    self.sell_model_search_cache.get(index, ""),
                )
            addable_model_ids = [model_id for model_id in visible_model_ids if model_id not in rule.model_ids]
            if self._draw_add_all_matches_button(
                f"sell_search_results_add_all_{index}",
                len(visible_model_ids),
                len(addable_model_ids),
            ):
                if self._set_sell_rule_model_ids(index, rule, rule.model_ids + addable_model_ids):
                    changed = True
            if picked_model_id > 0:
                if self._set_sell_rule_model_ids(index, rule, rule.model_ids + [picked_model_id]):
                    changed = True
                self.sell_model_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)

            if PyImGui.collapsing_header(f"Advanced##sell_advanced_{index}"):
                current_raw = self.sell_model_text_cache.get(index, _format_model_ids(rule.model_ids))
                new_raw = PyImGui.input_text(f"Manual Model IDs##sell_models_{index}", current_raw)
                if new_raw != current_raw:
                    self.sell_model_text_cache[index] = new_raw
                    parsed_model_ids = _dedupe_model_ids(_parse_model_ids(new_raw))
                    if self._set_sell_rule_model_ids(index, rule, parsed_model_ids):
                        changed = True
                self._draw_secondary_text("Use comma-separated model IDs only when the search picker is not enough.")

        PyImGui.spacing()
        same_kind_indices = self._get_sell_rule_indices_for_kind(rule.kind)
        same_kind_position = same_kind_indices.index(index) if index in same_kind_indices else -1
        move_up_target_index = same_kind_indices[same_kind_position - 1] if same_kind_position > 0 else -1
        move_down_target_index = same_kind_indices[same_kind_position + 1] if 0 <= same_kind_position < len(same_kind_indices) - 1 else -1

        PyImGui.begin_disabled(move_up_target_index < 0)
        move_up = PyImGui.small_button(f"Move Up##sell_move_up_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(move_down_target_index < 0)
        move_down = PyImGui.small_button(f"Move Down##sell_move_down_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        if PyImGui.button(f"Remove Rule##sell_remove_{index}"):
            self.sell_rules.pop(index)
            self.rule_ui_structure_changed = True
            self._refresh_rule_ui_caches()
            changed = True
            PyImGui.tree_pop()
            return changed
        if move_up:
            if self._move_rule_entry(self.sell_rules, index, move_up_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed
        if move_down:
            if self._move_rule_entry(self.sell_rules, index, move_down_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed

        PyImGui.tree_pop()
        return changed

    def _draw_destroy_rule_rarity_toggles(self, index: int, rule: DestroyRule) -> bool:
        changed = False
        PyImGui.text("Rarity Filters")
        rarity_options = _get_rarity_options_for_rule(rule.kind)
        for rarity_index, (rarity_key, rarity_label) in enumerate(rarity_options):
            current_value = bool(rule.rarities.get(rarity_key, False))
            new_value = PyImGui.checkbox(f"##destroy_rarity_{index}_{rarity_key}", current_value)
            if new_value != current_value:
                rule.rarities[rarity_key] = new_value
                changed = True
            PyImGui.same_line(0, 4)
            PyImGui.text_colored(rarity_label, RARITY_TEXT_COLORS.get(rarity_key, UI_COLOR_SUBTLE))
            if rarity_index % 2 == 0 and rarity_index + 1 < len(rarity_options):
                PyImGui.same_line(0, 12)
        return changed

    def _draw_destroy_runtime_controls(self) -> bool:
        changed = False
        self._draw_section_heading("Session Safety")
        self._draw_secondary_text("These toggles reset to off whenever Merchant Rules or its live config reloads.")

        instant_destroy_enabled = PyImGui.checkbox(
            "Instant Destroy (Session Only)##merchant_rules_destroy_instant",
            bool(self.destroy_instant_enabled),
        )
        if instant_destroy_enabled != self.destroy_instant_enabled:
            self.destroy_instant_enabled = instant_destroy_enabled
            changed = True
            if self.destroy_instant_enabled:
                self._request_instant_destroy_rescan()
            else:
                self.instant_destroy_rescan_requested = False

        include_protected_items = PyImGui.checkbox(
            "Include Protected Items (Session Only)##merchant_rules_destroy_include_protected",
            bool(self.destroy_include_protected_items),
        )
        if include_protected_items != self.destroy_include_protected_items:
            self.destroy_include_protected_items = include_protected_items
            changed = True
            if self.destroy_instant_enabled:
                self._request_instant_destroy_rescan()

        self._draw_secondary_text("Include Protected Items affects both Instant Destroy and Preview/Execute for this session only.")
        if self.destroy_instant_enabled:
            PyImGui.text_colored("Instant Destroy is active for this session.", UI_COLOR_DANGER)
        if self.destroy_include_protected_items:
            PyImGui.text_colored("Protected items can be destroyed in this session.", UI_COLOR_DANGER)
        if self.last_instant_destroy_summary:
            self._draw_secondary_text(self.last_instant_destroy_summary)
        return changed

    def _draw_destroy_rule_editor(self, index: int, rule: DestroyRule) -> bool:
        changed = False
        summary_text, ready = self._get_destroy_rule_summary(rule)
        state_label, state_color = self._get_rule_state_badge(enabled=bool(rule.enabled), ready=ready)
        type_label, type_color = self._get_rule_type_presentation(rule.kind)

        opened, enabled, _header_clicked = self._draw_rule_header_row(
            f"destroy_rule_header_{index}",
            f"{self._get_rule_display_label(rule, DESTROY_KIND_LABELS.get(rule.kind, 'Destroy Rule'))}###destroy_rule_{index}",
            type_label,
            type_color,
            summary_text,
            state_label,
            state_color,
            f"Enabled##destroy_enabled_{index}",
            bool(rule.enabled),
        )
        if enabled != rule.enabled:
            rule.enabled = enabled
            changed = True

        if not opened:
            return changed

        self._draw_section_heading("Basic")
        self._draw_secondary_text(
            f"Category: {DESTROY_RULE_WORKSPACE_LABELS.get(rule.kind, DESTROY_KIND_LABELS.get(rule.kind, 'Destroy Rule'))}",
            wrapped=False,
        )
        updated_rule_name = self._draw_rule_name_input(f"Rule Name (Optional)##destroy_rule_name_{index}", rule.name)
        if updated_rule_name != rule.name:
            rule.name = updated_rule_name
            changed = True

        if rule.kind in (DESTROY_KIND_WEAPONS, DESTROY_KIND_ARMOR):
            if rule.kind == DESTROY_KIND_WEAPONS:
                self._draw_secondary_text("Matching equippable weapons will be destroyed locally.")
            else:
                self._draw_secondary_text("Matching equippable armor pieces will be destroyed locally.")
            changed = self._draw_destroy_rule_rarity_toggles(index, rule) or changed
            self._draw_secondary_text("Protected items are skipped by default unless Include Protected Items is enabled for this session.")
        else:
            if rule.kind == DESTROY_KIND_MATERIALS:
                self._draw_secondary_text("Matching material stacks honor Keep Count by quantity. Preview blocks partial destroys when a safe split slot is unavailable.")
                if PyImGui.button(f"Add All Common Materials##destroy_common_preset_{index}"):
                    if self._set_destroy_rule_model_ids(index, rule, rule.model_ids + self._get_common_material_preset()):
                        changed = True
                PyImGui.same_line(0, 8)
                if PyImGui.button(f"Add All Rare Materials##destroy_rare_preset_{index}"):
                    if self._set_destroy_rule_model_ids(index, rule, rule.model_ids + self._get_rare_material_preset()):
                        changed = True
                if PyImGui.button(f"Replace With Common Materials##destroy_common_replace_{index}"):
                    if self._set_destroy_rule_model_ids(index, rule, self._get_common_material_preset()):
                        changed = True
                PyImGui.same_line(0, 8)
                if PyImGui.button(f"Replace With Rare Materials##destroy_rare_replace_{index}"):
                    if self._set_destroy_rule_model_ids(index, rule, self._get_rare_material_preset()):
                        changed = True
            else:
                self._draw_secondary_text("Matching inventory items are destroyed locally. Stackables honor Keep Count by quantity; non-stackables still use whole-item keeps.")

            if PyImGui.button(f"Clear List##destroy_clear_{index}"):
                if self._set_destroy_rule_model_ids(index, rule, []):
                    changed = True

            whitelist_targets = _normalize_whitelist_targets(getattr(rule, "whitelist_targets", []))
            selected_label = "Selected Materials" if rule.kind == DESTROY_KIND_MATERIALS else "Selected Items"
            item_column_label = "Material" if rule.kind == DESTROY_KIND_MATERIALS else "Item"
            empty_text = "No crafting materials selected yet." if rule.kind == DESTROY_KIND_MATERIALS else "No items selected yet."
            PyImGui.text(f"{selected_label}: {len(whitelist_targets)}")
            updated_targets, removed_model_id = self._draw_whitelist_targets(
                section_name="destroy_models",
                index=index,
                targets=whitelist_targets,
                item_column_label=item_column_label,
                empty_text=empty_text,
            )
            if removed_model_id > 0:
                if self._set_destroy_rule_model_ids(index, rule, [model_id for model_id in rule.model_ids if model_id != removed_model_id]):
                    changed = True
            elif self._set_destroy_rule_whitelist_targets(index, rule, updated_targets):
                changed = True

            search_text = self.destroy_model_search_cache.get(index, "")
            search_label = "Search Materials" if rule.kind == DESTROY_KIND_MATERIALS else "Search Items"
            updated_search_text = PyImGui.input_text(f"{search_label}##destroy_search_{index}", search_text)
            if updated_search_text != search_text:
                self.destroy_model_search_cache[index] = updated_search_text

            if rule.kind == DESTROY_KIND_MATERIALS:
                picked_model_id, visible_model_ids = self._draw_material_search_results(
                    f"destroy_search_results_{index}",
                    self.destroy_model_search_cache.get(index, ""),
                )
            else:
                picked_model_id, visible_model_ids = self._draw_search_results(
                    f"destroy_search_results_{index}",
                    self.destroy_model_search_cache.get(index, ""),
                )
            addable_model_ids = [model_id for model_id in visible_model_ids if model_id not in rule.model_ids]
            if self._draw_add_all_matches_button(
                f"destroy_search_results_add_all_{index}",
                len(visible_model_ids),
                len(addable_model_ids),
            ):
                if self._set_destroy_rule_model_ids(index, rule, rule.model_ids + addable_model_ids):
                    changed = True
            if picked_model_id > 0:
                if self._set_destroy_rule_model_ids(index, rule, rule.model_ids + [picked_model_id]):
                    changed = True
                self.destroy_model_search_cache[index] = self._get_model_name(picked_model_id) or str(picked_model_id)

            if PyImGui.collapsing_header(f"Advanced##destroy_advanced_{index}"):
                current_raw = self.destroy_model_text_cache.get(index, _format_model_ids(rule.model_ids))
                new_raw = PyImGui.input_text(f"Manual Model IDs##destroy_models_{index}", current_raw)
                if new_raw != current_raw:
                    self.destroy_model_text_cache[index] = new_raw
                    parsed_model_ids = _dedupe_model_ids(_parse_model_ids(new_raw))
                    if self._set_destroy_rule_model_ids(index, rule, parsed_model_ids):
                        changed = True
                self._draw_secondary_text("Use comma-separated model IDs only when the search picker is not enough.")

        PyImGui.spacing()
        same_kind_indices = self._get_destroy_rule_indices_for_kind(rule.kind)
        same_kind_position = same_kind_indices.index(index) if index in same_kind_indices else -1
        move_up_target_index = same_kind_indices[same_kind_position - 1] if same_kind_position > 0 else -1
        move_down_target_index = same_kind_indices[same_kind_position + 1] if 0 <= same_kind_position < len(same_kind_indices) - 1 else -1

        PyImGui.begin_disabled(move_up_target_index < 0)
        move_up = PyImGui.small_button(f"Move Up##destroy_move_up_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(move_down_target_index < 0)
        move_down = PyImGui.small_button(f"Move Down##destroy_move_down_{index}")
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        if PyImGui.button(f"Remove Rule##destroy_remove_{index}"):
            self.destroy_rules.pop(index)
            self.rule_ui_structure_changed = True
            self._refresh_rule_ui_caches()
            changed = True
            PyImGui.tree_pop()
            return changed
        if move_up:
            if self._move_rule_entry(self.destroy_rules, index, move_up_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed
        if move_down:
            if self._move_rule_entry(self.destroy_rules, index, move_down_target_index - index):
                changed = True
            PyImGui.tree_pop()
            return changed

        PyImGui.tree_pop()
        return changed

    def _draw_destroy_rules_section(self):
        runtime_changed = self._draw_destroy_runtime_controls()
        PyImGui.separator()

        section_changed = False
        self.rule_ui_structure_changed = False
        rule_counts = {
            kind: len(self._get_destroy_rule_indices_for_kind(kind))
            for kind in DESTROY_RULE_WORKSPACE_ORDER
        }
        self.active_destroy_rule_kind = self._draw_rule_kind_tabs(
            workspace_id="merchant_rules_destroy_kind",
            active_kind=self.active_destroy_rule_kind,
            kind_order=DESTROY_RULE_WORKSPACE_ORDER,
            tab_labels=DESTROY_RULE_WORKSPACE_LABELS,
            rule_counts=rule_counts,
        )
        PyImGui.separator()

        visible_indices = self._get_destroy_rule_indices_for_kind(self.active_destroy_rule_kind)
        section_label = DESTROY_RULE_WORKSPACE_LABELS.get(self.active_destroy_rule_kind, "Rules")
        self._draw_section_heading(f"Destroy: {section_label}")
        self._draw_secondary_text(
            f"Showing {len(visible_indices)} of {len(self.destroy_rules)} destroy rule(s). Move Up / Move Down stays within this section."
        )
        if PyImGui.button(f"Add {section_label} Rule##merchant_rules_add_destroy_{self.active_destroy_rule_kind}"):
            if self._append_destroy_rule_of_kind(self.active_destroy_rule_kind):
                visible_indices = self._get_destroy_rule_indices_for_kind(self.active_destroy_rule_kind)
                section_changed = True

        if not self.destroy_rules:
            self._draw_secondary_text("No destroy rules yet. Pick a section above and add the first rule for items you want removed permanently.")
        elif not visible_indices:
            self._draw_secondary_text(f"No {section_label.lower()} destroy rules in this section yet.")

        for visible_position, index in enumerate(list(visible_indices)):
            if index >= len(self.destroy_rules):
                break
            rule = self.destroy_rules[index]
            section_changed = self._draw_destroy_rule_editor(index, rule) or section_changed
            if self.rule_ui_structure_changed:
                break
            if visible_position + 1 < len(visible_indices):
                PyImGui.spacing()

        if runtime_changed:
            self._mark_preview_dirty("Destroy session settings changed. Preview again before execution.")
        if section_changed:
            self.destroy_rules = _normalize_destroy_rules(self.destroy_rules)
            self._rebuild_text_caches()
            self._save_profile()
            if self.destroy_instant_enabled:
                self._request_instant_destroy_rescan()
            self._mark_preview_dirty("Destroy rules changed. Preview again before execution.")

    def _draw_cleanup_workspace(self):
        cleanup_changed = False
        automation_changed = False
        cleanup_targets = _normalize_cleanup_targets(self.cleanup_targets)
        cleanup_sources = _normalize_cleanup_protection_sources(self.cleanup_protection_sources)

        self._draw_section_heading(CLEANUP_WORKSPACE_LABEL)
        self._draw_secondary_text(
            "Cleanup is the Xunlai deposit phase. It runs after sell and destroy resolution during Execute, and it can optionally auto-run once when you enter an outpost or Guild Hall."
        )

        auto_cleanup_enabled = PyImGui.checkbox(
            "Auto-run cleanup when entering an outpost or Guild Hall##merchant_rules_auto_cleanup_on_entry",
            bool(self.auto_cleanup_on_outpost_entry),
        )
        if auto_cleanup_enabled != self.auto_cleanup_on_outpost_entry:
            self.auto_cleanup_on_outpost_entry = auto_cleanup_enabled
            automation_changed = True
        run_cleanup_reason = self._get_action_block_reason("cleanup")
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(bool(run_cleanup_reason))
        run_cleanup_clicked = PyImGui.button("Run Cleanup Now##merchant_rules_cleanup_workspace_run_now")
        PyImGui.end_disabled()

        self._draw_secondary_text(
            f"Explicit targets: {len(cleanup_targets)} | Linked protection sources: {len(cleanup_sources)}",
            wrapped=False,
        )
        if run_cleanup_reason:
            self._draw_secondary_text(f"Run Cleanup Now: {run_cleanup_reason}")
        if self.last_cleanup_summary:
            self._draw_secondary_text(self.last_cleanup_summary)

        PyImGui.separator()
        self._draw_section_heading("Explicit Cleanup Targets")
        self._draw_secondary_text(
            "Pick exact item or material models to stash in Xunlai. Keep On Character is owned by cleanup settings and does not sync back to sell rules."
        )

        updated_targets = [
            CleanupTarget(
                model_id=int(target.model_id),
                keep_on_character=max(0, int(target.keep_on_character)),
            )
            for target in cleanup_targets
        ]
        display_targets = self._sort_targets_by_model_label_for_display(updated_targets)
        removed_cleanup_model_id = 0
        if updated_targets:
            child_height = min(220, 58 + (32 * len(updated_targets)))
            if PyImGui.begin_child("merchant_rules_cleanup_targets", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.begin_table("merchant_rules_cleanup_targets_table", 3, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Keep On Character", PyImGui.TableColumnFlags.WidthFixed, 150.0)
                    PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Item")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Keep On Character")
                    PyImGui.table_set_column_index(2)
                    PyImGui.text("Remove")

                    for target in display_targets:
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(self._format_model_label_short(target.model_id))

                        PyImGui.table_set_column_index(1)
                        PyImGui.push_item_width(140)
                        next_keep_count = PyImGui.input_int(
                            f"##merchant_rules_cleanup_keep_{target.model_id}",
                            int(target.keep_on_character),
                        )
                        PyImGui.pop_item_width()
                        target.keep_on_character = max(0, int(next_keep_count))

                        PyImGui.table_set_column_index(2)
                        if PyImGui.small_button(f"X##merchant_rules_cleanup_remove_{target.model_id}"):
                            removed_cleanup_model_id = int(target.model_id)
                            break
                    PyImGui.end_table()
            PyImGui.end_child()
        else:
            self._draw_secondary_text("No explicit cleanup targets yet.")

        if removed_cleanup_model_id > 0:
            updated_targets = [target for target in updated_targets if int(target.model_id) != removed_cleanup_model_id]
        if updated_targets != cleanup_targets:
            if self._set_cleanup_targets(updated_targets):
                cleanup_changed = True
                cleanup_targets = _normalize_cleanup_targets(self.cleanup_targets)

        updated_cleanup_search = PyImGui.input_text(
            "Search Items / Materials##merchant_rules_cleanup_search",
            self.cleanup_model_search_text,
        )
        if updated_cleanup_search != self.cleanup_model_search_text:
            self.cleanup_model_search_text = updated_cleanup_search

        picked_cleanup_model_id, visible_cleanup_model_ids = self._draw_search_results(
            "merchant_rules_cleanup_search_results",
            self.cleanup_model_search_text,
        )
        existing_cleanup_model_ids = {int(target.model_id) for target in cleanup_targets}
        addable_cleanup_model_ids = [
            int(model_id)
            for model_id in visible_cleanup_model_ids
            if int(model_id) not in existing_cleanup_model_ids
        ]
        if self._draw_add_all_matches_button(
            "merchant_rules_cleanup_add_all_matches",
            len(visible_cleanup_model_ids),
            len(addable_cleanup_model_ids),
        ):
            next_targets = list(cleanup_targets)
            for model_id in addable_cleanup_model_ids:
                next_targets.append(CleanupTarget(model_id=int(model_id), keep_on_character=0))
            if self._set_cleanup_targets(next_targets):
                cleanup_changed = True
                cleanup_targets = _normalize_cleanup_targets(self.cleanup_targets)

        if picked_cleanup_model_id > 0:
            if self._add_cleanup_target(picked_cleanup_model_id):
                cleanup_changed = True
                cleanup_targets = _normalize_cleanup_targets(self.cleanup_targets)
            self.cleanup_model_search_text = self._get_model_name(picked_cleanup_model_id) or str(picked_cleanup_model_id)

        PyImGui.separator()
        self._draw_section_heading("Linked Protection Sources")
        self._draw_secondary_text(
            "Link a weapon or armor sell rule here to deposit whatever that rule currently hard-protects during cleanup."
        )

        removed_cleanup_source_id = ""
        if cleanup_sources:
            child_height = min(220, 58 + (32 * len(cleanup_sources)))
            if PyImGui.begin_child("merchant_rules_cleanup_sources", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.begin_table("merchant_rules_cleanup_sources_table", 4, PyImGui.TableFlags.NoFlag):
                    PyImGui.table_setup_column("Sell Rule", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Status", PyImGui.TableColumnFlags.WidthFixed, 90.0)
                    PyImGui.table_setup_column("Jump", PyImGui.TableColumnFlags.WidthFixed, 92.0)
                    PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 60.0)

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Sell Rule")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text("Status")
                    PyImGui.table_set_column_index(2)
                    PyImGui.text("Jump")
                    PyImGui.table_set_column_index(3)
                    PyImGui.text("Remove")

                    for source in cleanup_sources:
                        safe_rule_id = _normalize_rule_id(source.sell_rule_id)
                        sell_rule_index = self._get_sell_rule_index_by_id(safe_rule_id)
                        sell_rule = self._get_sell_rule_by_id(safe_rule_id)
                        status_label = "Missing"
                        status_color = UI_COLOR_DANGER
                        rule_label = safe_rule_id or "Missing rule"
                        if sell_rule is not None and sell_rule_index >= 0:
                            rule_label = self._format_sell_rule_reference(sell_rule_index, sell_rule)
                            if sell_rule.kind not in (SELL_KIND_WEAPONS, SELL_KIND_ARMOR):
                                status_label = "Invalid"
                                status_color = UI_COLOR_WARNING
                            elif not sell_rule.enabled:
                                status_label = "Disabled"
                                status_color = UI_COLOR_WARNING
                            else:
                                status_label = "Ready"
                                status_color = UI_COLOR_SUCCESS

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(rule_label)

                        PyImGui.table_set_column_index(1)
                        PyImGui.text_colored(status_label, status_color)

                        PyImGui.table_set_column_index(2)
                        PyImGui.begin_disabled(sell_rule is None or sell_rule_index < 0)
                        jump_clicked = PyImGui.small_button(f"Jump To Rule##merchant_rules_cleanup_jump_{safe_rule_id}")
                        PyImGui.end_disabled()
                        if jump_clicked and sell_rule is not None and sell_rule_index >= 0:
                            subsection_anchor, target_key = self._get_default_sell_rule_protection_jump_target(sell_rule)
                            self._request_jump_to_sell_rule(
                                sell_rule_index,
                                sell_rule.kind,
                                subsection_anchor=subsection_anchor,
                                target_key=target_key,
                                requires_advanced=bool(subsection_anchor),
                            )

                        PyImGui.table_set_column_index(3)
                        if PyImGui.small_button(f"X##merchant_rules_cleanup_source_remove_{safe_rule_id}"):
                            removed_cleanup_source_id = safe_rule_id
                            break
                    PyImGui.end_table()
            PyImGui.end_child()
        else:
            self._draw_secondary_text("No linked protection sources yet.")

        if removed_cleanup_source_id:
            next_sources = [
                source
                for source in cleanup_sources
                if _normalize_rule_id(source.sell_rule_id) != removed_cleanup_source_id
            ]
            if self._set_cleanup_protection_sources(next_sources):
                cleanup_changed = True
                cleanup_sources = _normalize_cleanup_protection_sources(self.cleanup_protection_sources)

        linked_source_ids = {_normalize_rule_id(source.sell_rule_id) for source in cleanup_sources}
        available_linkable_rules = [
            sell_rule
            for sell_rule in self._get_cleanup_linkable_sell_rules()
            if _normalize_rule_id(getattr(sell_rule, "rule_id", "")) not in linked_source_ids
        ]
        if available_linkable_rules:
            self._draw_secondary_text("Available weapon and armor sell rules:")
            if PyImGui.begin_child("merchant_rules_cleanup_linkable_rules", (0, 120), True, PyImGui.WindowFlags.NoFlag):
                for sell_rule in available_linkable_rules:
                    safe_rule_id = _normalize_rule_id(getattr(sell_rule, "rule_id", ""))
                    sell_rule_index = self._get_sell_rule_index_by_id(safe_rule_id)
                    if PyImGui.small_button(f"Link##merchant_rules_cleanup_link_{safe_rule_id}"):
                        if self._add_cleanup_protection_source(safe_rule_id):
                            cleanup_changed = True
                            cleanup_sources = _normalize_cleanup_protection_sources(self.cleanup_protection_sources)
                    PyImGui.same_line(0, 8)
                    rule_label = self._format_sell_rule_reference(sell_rule_index, sell_rule)
                    state_suffix = "Enabled" if sell_rule.enabled else "Disabled"
                    self._draw_secondary_text(f"{rule_label} | {state_suffix}", wrapped=False)
            PyImGui.end_child()
        else:
            self._draw_secondary_text("No additional weapon or armor sell rules are available to link.")

        PyImGui.separator()
        self._draw_section_heading("Cleanup Preview")
        cleanup_preview_entries = [
            entry
            for entry in self.preview_plan.entries
            if str(entry.action_type) == "deposit" and str(entry.merchant_type) == MERCHANT_TYPE_STORAGE
        ]
        cleanup_actionable_entries, cleanup_skipped_entries = self._split_preview_entries(cleanup_preview_entries)
        if not self.preview_ready:
            self._draw_secondary_text("Run Preview Plan from Overview to refresh cleanup preview.")
        elif not cleanup_preview_entries:
            self._draw_secondary_text("No cleanup actions are currently planned.")
        else:
            self._draw_secondary_text(
                f"{len(cleanup_actionable_entries)} planned deposit step(s) | {len(cleanup_skipped_entries)} skipped",
                wrapped=False,
            )
            if cleanup_actionable_entries:
                self._draw_preview_entries_table(
                    "merchant_rules_cleanup_preview_actions",
                    cleanup_actionable_entries,
                )
            if cleanup_skipped_entries:
                if cleanup_actionable_entries:
                    PyImGui.spacing()
                if PyImGui.collapsing_header(
                    f"Skipped / blocked ({len(cleanup_skipped_entries)})##merchant_rules_cleanup_preview_skipped"
                ):
                    self._draw_preview_entries_table(
                        "merchant_rules_cleanup_preview_skipped_entries",
                        cleanup_skipped_entries,
                        show_reasons=True,
                        muted=True,
                    )

        if automation_changed:
            self._save_profile()
            self.status_message = (
                "Auto cleanup on outpost entry enabled."
                if self.auto_cleanup_on_outpost_entry
                else "Auto cleanup on outpost entry disabled."
            )
        if run_cleanup_clicked:
            self._queue_cleanup_now()
        if cleanup_changed:
            self._save_profile()
            self._mark_preview_dirty("Cleanup settings changed. Preview again before execution.")

    def _draw_buy_rules_section(self):
        section_changed = False
        self.rule_ui_structure_changed = False
        rule_counts = {
            kind: len(self._get_buy_rule_indices_for_kind(kind))
            for kind in BUY_RULE_WORKSPACE_ORDER
        }
        self.active_buy_rule_kind = self._draw_rule_kind_tabs(
            workspace_id="merchant_rules_buy_kind",
            active_kind=self.active_buy_rule_kind,
            kind_order=BUY_RULE_WORKSPACE_ORDER,
            tab_labels=BUY_RULE_WORKSPACE_LABELS,
            rule_counts=rule_counts,
        )
        PyImGui.separator()

        visible_indices = self._get_buy_rule_indices_for_kind(self.active_buy_rule_kind)
        section_label = BUY_RULE_WORKSPACE_LABELS.get(self.active_buy_rule_kind, "Rules")
        self._draw_section_heading(f"Buy: {section_label}")
        self._draw_secondary_text(
            f"Showing {len(visible_indices)} of {len(self.buy_rules)} buy rule(s). Move Up / Move Down stays within this section."
        )
        if PyImGui.button(f"Add {section_label} Rule##merchant_rules_add_buy_{self.active_buy_rule_kind}"):
            if self._append_buy_rule_of_kind(self.active_buy_rule_kind):
                visible_indices = self._get_buy_rule_indices_for_kind(self.active_buy_rule_kind)
                section_changed = True

        if not self.buy_rules:
            self._draw_secondary_text("No buy rules yet. Pick a section above and add the first rule to manage merchant stock, crafting materials, or rune trader stock.")
        elif not visible_indices:
            self._draw_secondary_text(f"No {section_label.lower()} buy rules in this section yet.")

        for visible_position, index in enumerate(list(visible_indices)):
            if index >= len(self.buy_rules):
                break
            rule = self.buy_rules[index]
            section_changed = self._draw_buy_rule_editor(index, rule) or section_changed
            if self.rule_ui_structure_changed:
                break
            if visible_position + 1 < len(visible_indices):
                PyImGui.spacing()

        if section_changed:
            self.buy_rules = _normalize_buy_rules(self.buy_rules)
            self._save_profile()
            self._mark_preview_dirty("Buy rules changed. Preview again before execution.")

    def _draw_sell_rules_section(self):
        section_changed = False
        self.rule_ui_structure_changed = False
        rule_counts = {
            kind: len(self._get_sell_rule_indices_for_kind(kind))
            for kind in SELL_RULE_WORKSPACE_ORDER
        }
        next_active_sell_rule_kind = self._draw_rule_kind_tabs(
            workspace_id="merchant_rules_sell_kind",
            active_kind=self.active_sell_rule_kind,
            kind_order=SELL_RULE_WORKSPACE_ORDER,
            tab_labels=SELL_RULE_WORKSPACE_LABELS,
            rule_counts=rule_counts,
        )
        self._set_active_sell_rule_kind(next_active_sell_rule_kind)
        PyImGui.separator()

        jump_target = self._get_sell_protection_jump_target()
        if jump_target is not None:
            self._debug_log(
                f"Protections jump entering sell rules section with active kind {self.active_sell_rule_kind} | "
                f"{self._format_sell_protection_jump_target_debug(jump_target)}"
            )

        visible_indices = self._get_sell_rule_indices_for_kind(self.active_sell_rule_kind)
        section_label = SELL_RULE_WORKSPACE_LABELS.get(self.active_sell_rule_kind, "Rules")
        self._draw_section_heading(f"Sell: {section_label}")
        self._draw_secondary_text(
            f"Showing {len(visible_indices)} of {len(self.sell_rules)} sell rule(s). Move Up / Move Down stays within this section."
        )
        if PyImGui.button(f"Add {section_label} Rule##merchant_rules_add_sell_{self.active_sell_rule_kind}"):
            if self._append_sell_rule_of_kind(self.active_sell_rule_kind):
                visible_indices = self._get_sell_rule_indices_for_kind(self.active_sell_rule_kind)
                section_changed = True

        if not self.sell_rules:
            self._draw_secondary_text("No sell rules yet. Pick a section above and add the first rule to manage items, materials, weapons, or armor.")
        elif not visible_indices:
            self._draw_secondary_text(f"No {section_label.lower()} sell rules in this section yet.")

        for visible_position, index in enumerate(list(visible_indices)):
            if index >= len(self.sell_rules):
                break
            rule = self.sell_rules[index]
            section_changed = self._draw_sell_rule_editor(index, rule) or section_changed
            if self.rule_ui_structure_changed:
                break
            if visible_position + 1 < len(visible_indices):
                PyImGui.spacing()

        jump_target = self._get_sell_protection_jump_target()
        if jump_target is not None:
            if int(jump_target.owner_rule_index) >= len(self.sell_rules):
                self._clear_sell_protection_jump("target rule index is no longer valid")
            elif str(jump_target.owner_rule_kind) != str(self.active_sell_rule_kind):
                self._clear_sell_protection_jump(
                    f"target owner kind {jump_target.owner_rule_kind} does not match active kind {self.active_sell_rule_kind}"
                )

        if section_changed:
            self._clear_sell_protection_jump("sell rule structure changed")
            self.sell_rules = _normalize_sell_rules(self.sell_rules)
            self._rebuild_text_caches()
            self._save_profile()
            self._mark_preview_dirty("Sell rules changed. Preview again before execution.")

    def _draw_preview_entries_table(
        self,
        table_id: str,
        entries: list[ExecutionPlanEntry],
        *,
        show_reasons: bool = False,
        muted: bool = False,
        plan: PlanResult | None = None,
        availability_here: dict[str, bool] | None = None,
    ):
        if not entries:
            return

        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
        if PyImGui.begin_table(table_id, 4, table_flags):
            PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.WidthFixed, 78.0)
            PyImGui.table_setup_column("Where", PyImGui.TableColumnFlags.WidthFixed, 118.0)
            PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Qty", PyImGui.TableColumnFlags.WidthFixed, 52.0)

            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            self._draw_secondary_text("Action", wrapped=False)
            PyImGui.table_set_column_index(1)
            self._draw_secondary_text("Where", wrapped=False)
            PyImGui.table_set_column_index(2)
            self._draw_secondary_text("Item", wrapped=False)
            PyImGui.table_set_column_index(3)
            self._draw_secondary_text("Qty", wrapped=False)

            for entry in entries:
                action_label = ACTION_TYPE_LABELS.get(str(entry.action_type), str(entry.action_type).title())
                is_conditional = str(entry.state) == PLAN_STATE_CONDITIONAL
                if is_conditional:
                    action_label = f"{action_label}*"
                quantity_text = "-" if int(entry.quantity) <= 0 else str(int(entry.quantity))
                available_here = self._is_preview_entry_available_here(
                    entry,
                    availability_here=availability_here,
                    plan=plan,
                )
                action_color = UI_COLOR_MUTED if muted else (UI_COLOR_SUCCESS if available_here else UI_COLOR_WARNING)
                text_color = UI_COLOR_MUTED if muted else (UI_COLOR_SUCCESS if available_here else UI_COLOR_WARNING)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text_colored(action_label, action_color)

                PyImGui.table_set_column_index(1)
                PyImGui.text_colored(MERCHANT_TYPE_LABELS.get(entry.merchant_type, str(entry.merchant_type)), text_color)

                PyImGui.table_set_column_index(2)
                item_label = self._format_preview_item_label(entry)
                if muted:
                    PyImGui.text_colored(item_label, UI_COLOR_MUTED)
                else:
                    PyImGui.text(item_label)
                unavailable_here_reason = ""
                if not muted:
                    unavailable_here_reason = self._get_preview_unavailable_here_reason(
                        entry,
                        availability_here=availability_here,
                        plan=plan,
                    )
                if unavailable_here_reason:
                    self._draw_secondary_text(unavailable_here_reason)
                displayed_reason = self._get_preview_reason_for_display(entry)
                if (show_reasons or is_conditional) and displayed_reason:
                    self._draw_secondary_text(displayed_reason)

                PyImGui.table_set_column_index(3)
                if muted:
                    PyImGui.text_colored(quantity_text, UI_COLOR_MUTED)
                else:
                    PyImGui.text(quantity_text)

            PyImGui.end_table()

    def _get_preview_reason_for_display(self, entry: ExecutionPlanEntry) -> str:
        reason = str(entry.reason or "").strip()
        if not reason or not self._preview_has_execute_travel_pending():
            return reason

        target_outpost_name = self.preview_execute_travel_target_outpost_name or "the selected outpost"
        suffix = self._get_projected_preview_reason_suffix(entry.merchant_type, target_outpost_name)
        if not suffix:
            return reason
        legacy_suffix = suffix.replace("Travel + Execute", "Execute") if suffix else ""
        if reason == suffix:
            return ""
        if legacy_suffix and reason == legacy_suffix:
            return ""
        spaced_suffix = f" {suffix}"
        if reason.endswith(spaced_suffix):
            return reason[: -len(spaced_suffix)].rstrip()
        if reason.endswith(suffix):
            return reason[: -len(suffix)].rstrip()
        if legacy_suffix:
            legacy_spaced_suffix = f" {legacy_suffix}"
            if reason.endswith(legacy_spaced_suffix):
                return reason[: -len(legacy_spaced_suffix)].rstrip()
            if reason.endswith(legacy_suffix):
                return reason[: -len(legacy_suffix)].rstrip()
        return reason

    def _draw_preview_section(self):
        actionable_entries, skipped_entries = self._split_preview_entries(self.preview_plan.entries)
        direct_count, conditional_count, skipped_count = self._get_preview_entry_counts(self.preview_plan.entries)
        availability_here = self._get_preview_here_availability() if self.preview_ready else {}
        self._draw_section_heading("Preview")
        if PyImGui.begin_child("MerchantRulesPreview", (0, 210), True, PyImGui.WindowFlags.NoFlag):
            if not self.preview_plan.entries:
                self._draw_secondary_text("Run Preview to see what Travel + Execute or Execute Here will do.")
            else:
                self._draw_secondary_text(
                    f"{direct_count} direct action(s) | {conditional_count} conditional action(s) | {skipped_count} blocked / skipped",
                    wrapped=False,
                )
                PyImGui.begin_disabled(not self.preview_ready)
                compare_clicked = PyImGui.small_button("Compare With Current Inventory##merchant_rules_compare_preview_inventory")
                PyImGui.end_disabled()
                if compare_clicked:
                    self._compare_current_inventory_against_preview()
                if self.preview_inventory_diff_summary:
                    diff_color = UI_COLOR_SUCCESS if not self.preview_inventory_diff_rows else UI_COLOR_WARNING
                    PyImGui.text_colored(self.preview_inventory_diff_summary, diff_color)
                    if self.preview_inventory_diff_rows:
                        for diff_row in self.preview_inventory_diff_rows:
                            self._draw_secondary_text(diff_row)
                if self._plan_needs_exact_storage_scan(self.preview_plan):
                    exact_scan_message = (
                        "Storage-aware planning is still partial. Use Open Xunlai for exact storage scan to turn storage-backed shortages into exact withdraw steps and direct Xunlai actions."
                        if self._can_use_local_storage_actions()
                        else "Storage-aware planning is still partial. Xunlai counts will stay estimated until Execute reaches an outpost or Guild Hall and can open storage."
                    )
                    PyImGui.text_colored(
                        exact_scan_message,
                        UI_COLOR_WARNING,
                    )
                    PyImGui.spacing()
                elif self._plan_has_conditional_cleanup_actions(self.preview_plan):
                    PyImGui.text_colored(
                        "* Planned Xunlai cleanup steps stay conditional until storage can be opened during Execute.",
                        UI_COLOR_WARNING,
                    )
                    PyImGui.spacing()
                if conditional_count > 0:
                    PyImGui.text_colored(
                        "* Conditional entries wait for live merchant or trader context. Merchant stock must be offered live, and Rune Trader buys depend on exact current trader offers.",
                        UI_COLOR_WARNING,
                    )
                    self._draw_secondary_text(
                        "Conditional means the service can be attempted, but live stock, trader offers, quotes, or Xunlai access still decide the final action."
                    )
                if self._preview_has_execute_travel_pending():
                    target_label = self.preview_execute_travel_target_outpost_name or "the selected outpost"
                    PyImGui.text_colored(
                        f"* Projected preview assumes Auto Travel reaches {target_label}. Travel + Execute will travel there and rebuild live before running merchant handling.",
                        UI_COLOR_INFO,
                    )
                    self._draw_secondary_text(
                        "Projected means this row comes from the target plan. Green rows can also run here; yellow rows still need travel or unresolved local service."
                    )
                if conditional_count > 0 or self._preview_has_execute_travel_pending():
                    PyImGui.spacing()
                if actionable_entries:
                    self._draw_preview_entries_table(
                        "merchant_preview_actions",
                        actionable_entries,
                        plan=self.preview_plan,
                        availability_here=availability_here,
                    )
                else:
                    self._draw_secondary_text("Nothing is currently ready to execute.")

                if skipped_entries:
                    if actionable_entries:
                        PyImGui.spacing()
                    if PyImGui.collapsing_header(f"Skipped / blocked ({len(skipped_entries)})##merchant_preview_skipped"):
                        self._draw_preview_entries_table(
                            "merchant_preview_skipped_entries",
                            skipped_entries,
                            show_reasons=True,
                            muted=True,
                            plan=self.preview_plan,
                            availability_here=availability_here,
                        )
        PyImGui.end_child()

    def _draw_overview_actions(self):
        self._draw_section_heading("Actions")
        preview_reason = self._get_action_block_reason("preview")
        execute_reason = self._get_action_block_reason("execute")
        execute_here_reason = self._get_action_block_reason("execute_here")
        cleanup_reason = self._get_action_block_reason("cleanup")

        PyImGui.begin_disabled(bool(preview_reason))
        preview_clicked = PyImGui.button("Preview Plan")
        PyImGui.end_disabled()

        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(bool(execute_reason) or self.execute_drift_requires_confirmation)
        execute_clicked = PyImGui.button("Travel + Execute")
        PyImGui.end_disabled()

        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(bool(execute_here_reason) or self.execute_drift_requires_confirmation)
        execute_here_clicked = PyImGui.button("Execute Here")
        PyImGui.end_disabled()

        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(bool(cleanup_reason))
        run_cleanup_clicked = PyImGui.button("Run Cleanup Now##merchant_rules_overview_run_cleanup")
        PyImGui.end_disabled()

        action_hint = (
            self.preview_inventory_diff_summary
            if self.execute_drift_requires_confirmation and self.preview_inventory_diff_summary
            else execute_reason or execute_here_reason or preview_reason or cleanup_reason
        )
        if action_hint:
            self._draw_secondary_text(action_hint)

        if self._can_run_preview_exact_storage_scan():
            PyImGui.begin_disabled(bool(preview_reason))
            storage_scan_clicked = PyImGui.button("Open Xunlai for exact storage scan")
            PyImGui.end_disabled()
        else:
            storage_scan_clicked = False

        if self.execute_drift_requires_confirmation:
            PyImGui.text_colored("Execution paused because inventory drift was detected after preview.", UI_COLOR_WARNING)
            for diff_row in self.preview_inventory_diff_rows:
                self._draw_secondary_text(diff_row)
            PyImGui.begin_disabled(bool(preview_reason))
            re_preview_clicked = PyImGui.button("Re-Preview##merchant_rules_execute_repreview")
            PyImGui.end_disabled()
            PyImGui.same_line(0, 8)
            PyImGui.begin_disabled(bool(execute_reason))
            execute_anyway_clicked = PyImGui.button("Execute Anyway##merchant_rules_execute_anyway")
            PyImGui.end_disabled()
        else:
            re_preview_clicked = False
            execute_anyway_clicked = False

        if preview_clicked:
            self._scan_preview()
        if execute_clicked:
            self._request_execute_now()
        if execute_here_clicked:
            self._request_execute_here()
        if run_cleanup_clicked:
            self._queue_cleanup_now()
        if re_preview_clicked:
            self._scan_preview()
        if execute_anyway_clicked:
            self._queue_execute_now()
        if storage_scan_clicked:
            GLOBAL_CACHE.Coroutines.append(self._open_xunlai_and_scan_preview())

    def _draw_overview_section(self):
        self._draw_status_section()
        PyImGui.separator()
        self._draw_travel_summary()
        PyImGui.separator()
        self._draw_overview_actions()
        if self._get_multibox_accounts():
            PyImGui.separator()
            if PyImGui.collapsing_header("Multibox##merchant_rules_multibox"):
                self._draw_multibox_section()
        PyImGui.separator()
        self._draw_preview_section()

    def _draw_profiles_workspace(self):
        current_payload_serialized = self._serialize_shareable_profile_payload(
            self._build_shareable_profile_payload()
        )
        selected_profile = self._get_selected_shared_profile()

        self._draw_section_heading("Shared Profiles")
        self._draw_secondary_text(
            "Shared profiles are named snapshots. Loading one applies it to this account's live Merchant Rules config, "
            "and cross-account updates stay explicit through Sync Rules to Selected."
        )
        live_config_label = (
            os.path.basename(self.config_path) if self.config_path else "Not initialized"
        )
        self._draw_secondary_text(f"Live Config: {live_config_label}", wrapped=False)
        self._draw_secondary_text(
            f"Library: {self._get_shared_profiles_dir()}",
            wrapped=False,
        )

        if self.shared_profile_warning:
            PyImGui.text_colored(
                f"Shared Profiles: {self.shared_profile_warning}",
                UI_COLOR_WARNING,
            )
        elif self.shared_profile_notice:
            self._draw_secondary_text(
                f"Shared Profiles: {self.shared_profile_notice}"
            )
        if self.shared_profile_scan_warning:
            PyImGui.text_colored(
                self.shared_profile_scan_warning,
                UI_COLOR_WARNING,
            )

        if PyImGui.small_button("Refresh Library##merchant_rules_shared_profiles_refresh"):
            self._refresh_shared_profile_entries()
            self._clear_shared_profile_confirmation_state()
            self._set_shared_profile_feedback(notice="Refreshed shared profile library.")
            selected_profile = self._get_selected_shared_profile()
        PyImGui.same_line(0, 8)
        if PyImGui.small_button("Open Profiles Folder##merchant_rules_shared_profiles_open_folder"):
            self._clear_shared_profile_confirmation_state()
            self._open_shared_profiles_folder()
            selected_profile = self._get_selected_shared_profile()

        self._draw_secondary_text(
            f"{len(self.shared_profile_entries)} shared profile(s), sorted alphabetically by display name.",
            wrapped=False,
        )
        PyImGui.separator()

        child_height = 220 if self.shared_profile_entries else 120
        if PyImGui.begin_child(
            "merchant_rules_shared_profiles_list",
            (0, child_height),
            True,
            PyImGui.WindowFlags.NoFlag,
        ):
            if not self.shared_profile_entries:
                self._draw_secondary_text(
                    "No shared profiles saved yet. Use Profile Name plus Save Current As New to create the first one."
                )
            else:
                for index, entry in enumerate(self.shared_profile_entries):
                    is_selected = (
                        os.path.normcase(os.path.normpath(entry.path))
                        == os.path.normcase(
                            os.path.normpath(self.shared_profile_selected_path)
                        )
                    )
                    if PyImGui.selectable(
                        f"{entry.display_name}##merchant_rules_shared_profile_{index}",
                        is_selected,
                        PyImGui.SelectableFlags.NoFlag,
                        (0, 0),
                    ):
                        self._set_selected_shared_profile_path(entry.path)
                        selected_profile = self._get_selected_shared_profile()
                    state_label = (
                        "Matches Current"
                        if entry.serialized_payload == current_payload_serialized
                        else "Different From Current"
                    )
                    self._draw_secondary_text(
                        (
                            f"Saved: {entry.saved_at_label or 'Unknown'} | "
                            f"{state_label} | File: {entry.filename}"
                        ),
                        wrapped=False,
                    )
                    if index + 1 < len(self.shared_profile_entries):
                        PyImGui.separator()
        PyImGui.end_child()

        selected_profile = self._get_selected_shared_profile()
        PyImGui.separator()
        self._draw_section_heading("Selected Profile")
        if selected_profile is None:
            self._draw_secondary_text(
                "Select a shared profile to load, rename, overwrite, or delete."
            )
        else:
            match_selected_label = (
                "Matches the current live config"
                if selected_profile.serialized_payload == current_payload_serialized
                else "Differs from the current live config"
            )
            match_color = (
                UI_COLOR_SUCCESS
                if selected_profile.serialized_payload == current_payload_serialized
                else UI_COLOR_WARNING
            )
            PyImGui.text(f"Name: {selected_profile.display_name}")
            if selected_profile.saved_at_label:
                self._draw_secondary_text(
                    f"Saved: {selected_profile.saved_at_label}",
                    wrapped=False,
                )
            PyImGui.text_colored(match_selected_label, match_color)
            self._draw_secondary_text(
                "Load applies this snapshot locally. Use Sync Rules to Selected afterward if you want followers updated."
            )

        updated_profile_name = PyImGui.input_text(
            "Profile Name##merchant_rules_shared_profile_name",
            self.shared_profile_name_input,
        )
        if updated_profile_name != self.shared_profile_name_input:
            self.shared_profile_name_input = updated_profile_name

        self._draw_secondary_text(
            "Save Current As New creates a new shared snapshot. Rename changes only the saved profile's display name. "
            "Save Current Over Selected updates the chosen snapshot with your current local Merchant Rules config."
        )

        rename_disabled = selected_profile is None
        load_disabled = selected_profile is None
        overwrite_disabled = selected_profile is None
        delete_disabled = selected_profile is None
        normalized_selected_path = (
            os.path.normcase(os.path.normpath(selected_profile.path))
            if selected_profile is not None
            else ""
        )
        overwrite_confirm_required = bool(
            normalized_selected_path
            and normalized_selected_path
            == os.path.normcase(
                os.path.normpath(self.shared_profile_pending_overwrite_path)
            )
        )
        delete_confirm_required = bool(
            normalized_selected_path
            and normalized_selected_path
            == os.path.normcase(
                os.path.normpath(self.shared_profile_pending_delete_path)
            )
        )

        save_new_clicked = PyImGui.button(
            "Save Current As New##merchant_rules_shared_profile_save_new"
        )
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(rename_disabled)
        rename_clicked = PyImGui.button(
            "Rename Selected##merchant_rules_shared_profile_rename"
        )
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(load_disabled)
        load_clicked = PyImGui.button(
            "Load Selected##merchant_rules_shared_profile_load"
        )
        PyImGui.end_disabled()

        overwrite_label = (
            "Click Again to Save Over Selected##merchant_rules_shared_profile_overwrite"
            if overwrite_confirm_required
            else "Save Current Over Selected##merchant_rules_shared_profile_overwrite"
        )
        delete_label = (
            "Click Again to Delete Selected##merchant_rules_shared_profile_delete"
            if delete_confirm_required
            else "Delete Selected##merchant_rules_shared_profile_delete"
        )

        PyImGui.begin_disabled(overwrite_disabled)
        overwrite_clicked = PyImGui.button(overwrite_label)
        PyImGui.end_disabled()
        PyImGui.same_line(0, 8)
        PyImGui.begin_disabled(delete_disabled)
        delete_clicked = PyImGui.button(delete_label)
        PyImGui.end_disabled()

        if save_new_clicked:
            self._clear_shared_profile_confirmation_state()
            self._save_current_as_new_shared_profile()
            selected_profile = self._get_selected_shared_profile()
        if rename_clicked:
            self._clear_shared_profile_confirmation_state()
            self._rename_selected_shared_profile()
            selected_profile = self._get_selected_shared_profile()
        if load_clicked:
            self._clear_shared_profile_confirmation_state()
            self._load_selected_shared_profile()
            selected_profile = self._get_selected_shared_profile()
        if overwrite_clicked and selected_profile is not None:
            if overwrite_confirm_required:
                self._save_current_over_selected_shared_profile()
            else:
                self.shared_profile_pending_overwrite_path = selected_profile.path
                self.shared_profile_pending_delete_path = ""
                self._set_shared_profile_feedback(
                    notice=(
                        f"Click overwrite again to replace shared profile "
                        f"'{selected_profile.display_name}'."
                    )
                )
            selected_profile = self._get_selected_shared_profile()
        if delete_clicked and selected_profile is not None:
            if delete_confirm_required:
                self._delete_selected_shared_profile()
            else:
                self.shared_profile_pending_delete_path = selected_profile.path
                self.shared_profile_pending_overwrite_path = ""
                self._set_shared_profile_feedback(
                    notice=(
                        f"Click delete again to remove shared profile "
                        f"'{selected_profile.display_name}'."
                    )
                )

        PyImGui.separator()
        self._draw_section_heading("Live Config")
        self._draw_secondary_text(
            "The current account keeps a separate live working config. Live Config Recovery restores that file "
            "and its last automatic backup without changing the shared profiles library."
        )
        if self.profile_warning:
            PyImGui.text_colored(
                f"Live Config: {self.profile_warning}",
                UI_COLOR_WARNING,
            )
        elif self.profile_notice:
            self._draw_secondary_text(f"Live Config: {self.profile_notice}")
        if PyImGui.collapsing_header("Live Config Recovery##merchant_rules_live_config_recovery"):
            self._draw_live_config_recovery_section()

    def _draw_rules_workspace(self):
        if (
            self.active_rules_workspace != RULES_WORKSPACE_CLEANUP
            and not (self.buy_rules or self.sell_rules or self.destroy_rules)
            and self._has_cleanup_sources()
        ):
            self.active_rules_workspace = RULES_WORKSPACE_CLEANUP

        if self._draw_workspace_button("Buy", active=self.active_rules_workspace == RULES_WORKSPACE_BUY, color=UI_COLOR_TAB_ACTIVE):
            self._set_active_rules_workspace(RULES_WORKSPACE_BUY)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button("Sell", active=self.active_rules_workspace == RULES_WORKSPACE_SELL, color=UI_COLOR_TAB_ACTIVE):
            self._set_active_rules_workspace(RULES_WORKSPACE_SELL)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button(CLEANUP_WORKSPACE_LABEL, active=self.active_rules_workspace == RULES_WORKSPACE_CLEANUP, color=UI_COLOR_INFO):
            self._set_active_rules_workspace(RULES_WORKSPACE_CLEANUP)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button("Protections", active=self.active_rules_workspace == RULES_WORKSPACE_PROTECTIONS, color=UI_COLOR_INFO):
            self._set_active_rules_workspace(RULES_WORKSPACE_PROTECTIONS)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button("Destroy", active=self.active_rules_workspace == RULES_WORKSPACE_DESTROY, color=UI_COLOR_DANGER):
            self._set_active_rules_workspace(RULES_WORKSPACE_DESTROY)

        PyImGui.separator()
        if self._should_show_guided_empty_state():
            self._draw_guided_empty_state()
            return

        if self.active_rules_workspace == RULES_WORKSPACE_BUY:
            diagnostics = self._get_buy_rule_overlap_diagnostics()
            if diagnostics:
                self._draw_rule_overlap_diagnostics(diagnostics)
                PyImGui.separator()
            self._draw_buy_rules_section()
        elif self.active_rules_workspace == RULES_WORKSPACE_SELL:
            diagnostics = self._get_sell_rule_overlap_diagnostics()
            if diagnostics:
                self._draw_rule_overlap_diagnostics(diagnostics)
                PyImGui.separator()
            self._draw_sell_rules_section()
        elif self.active_rules_workspace == RULES_WORKSPACE_CLEANUP:
            self._draw_cleanup_workspace()
        elif self.active_rules_workspace == RULES_WORKSPACE_PROTECTIONS:
            self._draw_protections_section()
        else:
            diagnostics = self._get_destroy_rule_overlap_diagnostics()
            if diagnostics:
                self._draw_rule_overlap_diagnostics(diagnostics)
                PyImGui.separator()
            self._draw_destroy_rules_section()

    def draw(self):
        self._tick_runtime()
        floating_button = self._ensure_floating_ui()
        floating_button.draw(self.floating_ui_ini_key)
        self.show_main_window = bool(floating_button.visible)
        if not self.show_main_window:
            return

        if not self._draw_main_window():
            return

        if self._draw_workspace_button("Overview", active=self.active_workspace == WORKSPACE_OVERVIEW, color=UI_COLOR_TAB_ACTIVE):
            self._set_active_workspace(WORKSPACE_OVERVIEW)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button("Rules", active=self.active_workspace == WORKSPACE_RULES, color=UI_COLOR_TAB_ACTIVE):
            self._set_active_workspace(WORKSPACE_RULES)
        PyImGui.same_line(0, 8)
        if self._draw_workspace_button("Profiles", active=self.active_workspace == WORKSPACE_PROFILES, color=UI_COLOR_INFO):
            self._set_active_workspace(WORKSPACE_PROFILES)

        PyImGui.separator()
        if self.active_workspace == WORKSPACE_OVERVIEW:
            self._draw_overview_section()
        elif self.active_workspace == WORKSPACE_PROFILES:
            self._draw_profiles_workspace()
        else:
            self._draw_rules_workspace()
        PyImGui.end()


WIDGET_INSTANCE = MerchantRulesWidget()


def main():
    WIDGET_INSTANCE.draw()


def on_enable():
    WIDGET_INSTANCE.on_enable()


def tooltip():
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.bullet_text("Single-account merchant planner with optional auto-travel.")
    PyImGui.bullet_text("Weapon and armor sell rules can filter by rarity and protect items with selected mods, runes, or insignias.")
    PyImGui.bullet_text("Pinned travel targets and searchable outpost selection.")
    PyImGui.bullet_text("Preview projects the full post-travel merchant plan without moving the character.")
    PyImGui.bullet_text("Optional auto-travel to a selected outpost before merchant handling.")
    PyImGui.bullet_text("Top-level Overview, Rules, and Profiles workspaces, with live-config recovery under Profiles.")
    PyImGui.bullet_text("Cleanup / Xunlai is a separate workspace with explicit stash targets, linked protection sources, and optional outpost-entry auto cleanup.")
    PyImGui.bullet_text("Protections is a central hub over current sell-owned protection entries, with owner state, rule order, and Jump to Rule.")
    PyImGui.bullet_text("Destroy supports Preview -> Execute plus session-only Instant Destroy and Include Protected Items toggles.")
    PyImGui.bullet_text("Leader-driven multibox sync, preview, and execute for selected active accounts.")
    PyImGui.bullet_text("Shared named profiles load locally first, then propagate only through explicit Sync Rules to Selected.")
    PyImGui.bullet_text("Standalone weapon mods, runes, and insignias can route through Rune Trader when found.")
    PyImGui.bullet_text("Uses main-branch merchant routines.")
    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()
