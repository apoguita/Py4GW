import json
import os
import re
import shutil
import traceback
from collections import OrderedDict
from pathlib import Path

import Py4GW  # type: ignore
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Color
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import DyeColor
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Map, Player
from Py4GWCoreLib import get_texture_for_model
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums import ModelID

# region Frenkey Function

try:
    # We will try to use LootEx to generate Known items
    # https://github.com/frenkey-derp/Py4GW/tree/apo_source/Widgets/frenkey
    # This will require you to download and add to your file `Core` and `LootEx`
    from Widgets.frenkey.LootEx.data import Data  # type: ignore
    from Widgets.frenkey.LootEx.utility import Util  # type: ignore

    LOOTEX_AVAILABLE = True

except Exception:
    Util = None
    Data = None

    LOOTEX_AVAILABLE = False

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))


BASE_DIR = os.path.join(project_root, "Widgets/Config")
DB_BASE_DIR = os.path.join(project_root, "Widgets/Data")
JSON_INVENTORY_PATH = os.path.join(DB_BASE_DIR, "Inventory")
JSON_INVENTORY_MODEL_IDS_PATH = os.path.join(DB_BASE_DIR, "InventoryModelIds")
JSON_INVENTORY_MOD_HASH_PATH = os.path.join(DB_BASE_DIR, "InventoryModHash")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "team_inventory_viewer.ini")
os.makedirs(BASE_DIR, exist_ok=True)

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()
inventory_write_timer = ThrottledTimer(3000)
inventory_read_timer = ThrottledTimer(5000)
name_request_timer = ThrottledTimer(1000)

# String consts
MODULE_NAME = "TeamInventoryViewer"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 1512)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 0)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, True)

# View data
first_run = True
on_first_load = True
all_accounts_search_query = ''
search_query = ''
current_character_name = ''

TEAM_INVENTORY_CACHE = {}
INVENTORY_MODEL_ID_CACHE = {}
INVENTORY_MOD_HASH_CACHE = {}

INVENTORY_BAGS = {
    "Backpack": Bags.Backpack.value,
    "BeltPouch": Bags.BeltPouch.value,
    "Bag1": Bags.Bag1.value,
    "Bag2": Bags.Bag2.value,
    "EquipmentPack": Bags.EquipmentPack.value,
    "EquippedItems": Bags.EquippedItems.value,
}

STORAGE_BAGS = {
    "Storage1": Bags.Storage1.value,
    "Storage2": Bags.Storage2.value,
    "Storage3": Bags.Storage3.value,
    "Storage4": Bags.Storage4.value,
    "Storage5": Bags.Storage5.value,
    "Storage6": Bags.Storage6.value,
    "Storage7": Bags.Storage7.value,
    "Storage8": Bags.Storage8.value,
    "Storage9": Bags.Storage9.value,
    "Storage10": Bags.Storage10.value,
    "Storage11": Bags.Storage11.value,
    "Storage12": Bags.Storage12.value,
    "Storage13": Bags.Storage13.value,
    "Storage14": Bags.Storage14.value,
    "MaterialStorage": Bags.MaterialStorage.value,
}

ATTRIBUTES = {
    "Axe Mastery",
    "Hammer Mastery",
    "Swordsmanship",
    "Tactics",
    "Strength",
    "Marksmanship",
    "Beast Mastery",
    "Wilderness Survival",
    "Expertise",
    "Divine Favor",
    "Healing Prayers",
    "Protection Prayers",
    "Smiting Prayers",
    "Blood Magic",
    "Curses",
    "Death Magic",
    "Soul Reaping",
    "Domination Magic",
    "Fast Casting",
    "Illusion Magic",
    "Inspiration Magic",
    "Energy Storage",
    "Air Magic",
    "Earth Magic",
    "Fire Magic",
    "Water Magic",
    "Critical Strikes",
    "Dagger Mastery",
    "Deadly Arts",
    "Shadow Arts",
    "Channeling Magic",
    "Communing",
    "Restoration Magic",
    "Spawning Power",
    "Command",
    "Leadership",
    "Motivation",
    "Spear Mastery",
    "Earth Prayers",
    "Mysticism",
    "Scythe Mastery",
    "Wind Prayers",
}

# 1. Armor runes → "of Vitae", "of Major Vigor", "of Superior Soul Reaping", …
NON_ATTRIBUTE_RUNES = {"Vitae", "Vigor", "Attunement", "Clarity", "Purity", "Recovery", "Restoration", "Absorption"}
ARMOR_RUNE_SUFFIXES = {
    f"of {mod}{rune}" for rune in ATTRIBUTES | NON_ATTRIBUTE_RUNES for mod in ["", "Minor ", "Major ", "Superior "]
}

# 2. Weapon grips / handles / inscriptions → "Grip of Axe Mastery", "Handle of Soul Reaping", …
WEAPON_ATTRIBUTE_SUFFIXES = {f"of {attr}" for attr in ATTRIBUTES}

OTHER_WEAPON_SUFFIXES = {
    "of Defense",
    "of Shelter",
    "of Warding",
    "of Enchanting",
    "of Swiftness",
    "of Aptitude",
    "of Fortitude",
    "of Devotion",
    "of Endurance",
    "of Valor",
    "of Mastery",
    "of Quickening",
    "of Memory",
    # Profession
    "of the Warrior",
    "of the Ranger",
    "of the Necromancer",
    "of the Elementalist",
    "of the Mesmer",
    "of the Monk",
    "of the Ritualist",
    "of the Assassin",
    "of the Paragon",
    "of the Dervish",
    # Slaying
    "of Charrslaying",
    "of Demonslaying",
    "of Dragonslaying",
    "of Dwarfslaying",
    "of Giantslaying",
    "of Ogreslaying",
    "of Pruning",
    "of Tenguslaying",
    "of Trollslaying",
    "of Undeadbane",
    "of Skeletonslaying",
    "of Deathbane",
}

ALL_SUFFIXES = ARMOR_RUNE_SUFFIXES | WEAPON_ATTRIBUTE_SUFFIXES | OTHER_WEAPON_SUFFIXES

WEAPON_PREFIXES = {
    "Barbed",
    "Crippling",
    "Cruel",
    "Heavy",
    "Poisonous",
    "Silencing",
    "Ebon",
    "Fiery",
    "Icy",
    "Shocking",
    "Furious",
    "Sundering",
    "Vampiric",
    "Zealous",
    "Adept",
    "Defensive",
    "Hale",
    "Insightful",
    "Swift",
}

INSIGNIAS = {
    "Survivor",
    "Radiant",
    "Stalwart",
    "Brawler's",
    "Blessed",
    "Herald's",
    "Sentry's",
    "Knight's",
    "Stonefist",
    "Dreadnought",
    "Sentinel's",
    "Lieutenant's",
    "Frostbound",
    "Pyrebound",
    "Stormbound",
    "Scout's",
    "Earthbound",
    "Beastmaster's",
    "Wanderer's",
    "Disciple's",
    "Anchorite's",
    "Bloodstained",
    "Tormentor's",
    "Bonelace",
    "Minion Master's",
    "Blighter's",
    "Undertaker's",
    "Virtuoso's",
    "Artificer's",
    "Prodigy's",
    "Hydromancer",
    "Geomancer",
    "Pyromancer",
    "Aeromancer",
    "Prismatic",
    "Vanguard's",
    "Infiltrator's",
    "Saboteur's",
    "Nightstalker's",
    "Shaman's",
    "Ghostforge",
    "Mystic's",
    "Centurion's",
    "Windwalker",
    "Forsaken",
}


def clean_gw_item_name(item_name: str):
    """
    PERFECT Guild Wars 1 item name cleaner for weapons AND armor.
    - Removes at most one prefix/insignia + one suffix/rune.
    - Supports partial matches like: 'Survivor' -> "Survivor's"
    - Returns: (base_name, removed_prefix, removed_suffix)
    """
    if not item_name:
        return "", None, None

    words = item_name.strip().split()
    if not words:
        return "", None, None

    result = []
    removed_prefix = None
    removed_suffix = None

    i = 0
    n = len(words)

    # Normalize prefix/insignia list for flexible matching
    all_prefixes = WEAPON_PREFIXES | INSIGNIAS
    normalized_prefixes = {p.lower().rstrip("'s") for p in all_prefixes}

    if i < n:
        original = words[i].rstrip(".,!?")
        normalized = original.lower().rstrip("'s")

        if normalized in normalized_prefixes:
            removed_prefix = original  # store EXACT original prefix
            i += 1

    while i < n:
        remaining = words[i:]
        suffix_matched = False

        # Try longest suffix first (up to 5 words)
        for length in range(min(5, len(remaining)), 0, -1):
            candidate = " ".join(remaining[:length]).rstrip(".,!?")
            if candidate in ALL_SUFFIXES:
                removed_suffix = candidate  # store EXACT matched suffix phrase
                suffix_matched = True
                break

        if suffix_matched:
            break

        result.append(words[i])
        i += 1

    # Final cleanup of base name
    base_name = " ".join(result).strip()
    base_name = ''.join(c for c in base_name if not c.isdigit())

    return base_name, removed_prefix, removed_suffix


# endregion


# region JSONStore
class ModelIDJSONStore:
    def __init__(self):
        self.path = Path(JSON_INVENTORY_MODEL_IDS_PATH)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.path / "model_ids.json"
        self.backup_path = self.file_path.with_suffix(".json.bak")

    def _read(self):
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, "r") as f:
                return json.load(f, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            if self.backup_path.exists():
                try:
                    with open(self.backup_path, "r") as f:
                        return json.load(f, object_pairs_hook=OrderedDict)
                except Exception:
                    pass
            return {}

    def _write(self, data):
        if not Routines.Checks.Map.MapValid():
            # Skip writing while map is invalid
            return False

        temp_file = self.file_path.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            if self.file_path.exists():
                shutil.copy2(self.file_path, self.backup_path)
            os.replace(temp_file, self.file_path)
            return True
        except Exception as e:
            ConsoleLog("ModelIDJSONStore", f"[WARN] Failed to write {self.file_path}: {e}")
            return False

    def save_model_id(self, model_id, model_name):
        str_model_id = str(model_id)
        data = self._read()
        if model_id and model_name:
            data[str_model_id] = model_name
            INVENTORY_MODEL_ID_CACHE[str_model_id] = model_name
            self._write(data)

    def load(self):
        global INVENTORY_MODEL_ID_CACHE

        if INVENTORY_MODEL_ID_CACHE:
            return INVENTORY_MODEL_ID_CACHE

        data = self._read()
        keys_to_delete = []
        for key, value in data.items():
            if not value:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del data[key]

        INVENTORY_MODEL_ID_CACHE = data
        return data


class ModHashJSONStore:
    def __init__(self):
        self.path = Path(JSON_INVENTORY_MOD_HASH_PATH)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.path / "mod_hash.json"
        self.backup_path = self.file_path.with_suffix(".json.bak")

    @staticmethod
    def hash_mods(modifiers):
        """
        Generates a stable 64-bit hash for a list of modifier objects.
        Extracts identifier + args + modbits from each mod.
        """

        def safe_int(v):
            try:
                return int(v)
            except Exception:
                return 0  # fallback for None or weird values

        # Build the integer matrix
        data = []
        for mod in modifiers:
            data.append([
                safe_int(mod.GetIdentifier()),
                safe_int(mod.GetArg1()),
                safe_int(mod.GetArg2()),
                safe_int(mod.GetArg()),
                safe_int(mod.GetModBits()),
            ])

        # === Fast 64-bit hash mixer ===
        h = 0
        for lst in data:
            for num in lst:
                h = (h * 1315423911) ^ num ^ (h >> 5)
                h &= 0xFFFFFFFFFFFFFFFF  # keep 64 bits

        return hex(h)[2:]

    def _read(self):
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, "r") as f:
                return json.load(f, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            if self.backup_path.exists():
                try:
                    with open(self.backup_path, "r") as f:
                        return json.load(f, object_pairs_hook=OrderedDict)
                except Exception:
                    pass
            return {}

    def _write(self, data):
        if not Routines.Checks.Map.MapValid():
            # Skip writing while map is invalid
            return False

        temp_file = self.file_path.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            if self.file_path.exists():
                shutil.copy2(self.file_path, self.backup_path)
            os.replace(temp_file, self.file_path)
            return True
        except Exception as e:
            ConsoleLog("ModelHashJSONStore", f"[WARN] Failed to write {self.file_path}: {e}")
            return False

    def save_mod_hash(self, mod_hash, prefix=None, suffix=None):
        str_mod_hash = str(mod_hash)
        data = self._read()
        if mod_hash and (prefix or suffix):
            data[str_mod_hash] = [prefix, suffix]
            INVENTORY_MOD_HASH_CACHE[str_mod_hash] = [prefix, suffix]
            self._write(data)

    def load(self):
        global INVENTORY_MOD_HASH_CACHE

        if INVENTORY_MOD_HASH_CACHE:
            return INVENTORY_MOD_HASH_CACHE

        data = self._read()
        keys_to_delete = []
        for key, value in data.items():
            if not value:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del data[key]

        INVENTORY_MOD_HASH_CACHE = data
        return data


class AccountJSONStore:
    def __init__(self, email):
        self.email = email
        self.path = Path(JSON_INVENTORY_PATH)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.path / f"{self.email}.json"
        self.backup_path = self.file_path.with_suffix(".json.bak")

    def _read(self):
        if not self.file_path.exists():
            return {"Characters": OrderedDict(), "Storage": OrderedDict()}

        try:
            with open(self.file_path, "r") as f:
                return json.load(f, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            if self.backup_path.exists():
                try:
                    with open(self.backup_path, "r") as f:
                        return json.load(f, object_pairs_hook=OrderedDict)
                except Exception:
                    pass
            return {"Characters": OrderedDict(), "Storage": OrderedDict()}

    def _write(self, data):
        if not Routines.Checks.Map.MapValid():
            # Skip writing while map is invalid
            return False

        temp_file = self.file_path.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            if self.file_path.exists():
                shutil.copy2(self.file_path, self.backup_path)
            os.replace(temp_file, self.file_path)
            return True
        except Exception as e:
            ConsoleLog("AccountJSONStore", f"[WARN] Failed to write {self.file_path}: {e}")
            return False

    def _deep_dict_equal(self, a, b):
        """
        Recursively checks if two dictionaries (or nested structures) are equal.
        Supports dicts, OrderedDicts, and lists.
        """
        if isinstance(a, dict) or isinstance(a, OrderedDict):
            if a.keys() != b.keys():
                return False
            return all(self._deep_dict_equal(a[k], b[k]) for k in a)

        if isinstance(a, list):
            if len(a) != len(b):
                return False
            return all(self._deep_dict_equal(x, y) for x, y in zip(a, b))

        # Base case: primitive types
        return a == b

    # --- Cached interface ---
    def load(self):
        if self.email in TEAM_INVENTORY_CACHE:
            return TEAM_INVENTORY_CACHE[self.email]

        data = self._read()
        TEAM_INVENTORY_CACHE[self.email] = data
        return data

    def save_bag(self, char_name=None, storage_name=None, bag_name=None, bag_items={}):
        data = self._read()
        changed = False

        if char_name:
            chars = data["Characters"]
            if char_name not in chars:
                chars[char_name] = {"Inventory": OrderedDict()}
            inv = chars[char_name]["Inventory"]
            if not self._deep_dict_equal(inv.get(bag_name), bag_items):
                inv[bag_name] = bag_items
                changed = True
        elif storage_name:
            storage = data["Storage"]
            if not self._deep_dict_equal(storage.get(storage_name), bag_items):
                storage[storage_name] = bag_items
                changed = True

        if changed:
            TEAM_INVENTORY_CACHE[self.email] = data
            self._write(data)

    def clear_character(self, char_name):
        if not self.file_path.exists():
            return

        try:
            data = self._read()
            chars = data.get("Characters", {})
            if char_name in chars:
                del chars[char_name]
                self._write(data)
                ConsoleLog("AccountJSONStore", f"Removed character {char_name} from {self.email}.")
            else:
                ConsoleLog("AccountJSONStore", f"[WARN] Character {char_name} not found for {self.email}.")
            TEAM_INVENTORY_CACHE[self.email] = data
        except Exception as e:
            ConsoleLog("AccountJSONStore", f"[ERROR] clear_character: {e}")

    def clear_account(self):
        try:
            if self.file_path.exists():
                self.file_path.unlink()
            if self.backup_path.exists():
                self.backup_path.unlink()
            TEAM_INVENTORY_CACHE[self.email] = None
            ConsoleLog("AccountJSONStore", f"Cleared all data for {self.email}.")
        except Exception as e:
            ConsoleLog("AccountJSONStore", f"[WARN] Failed to clear account {self.email}: {e}")


class MultiAccountInventoryStore:
    def __init__(self):
        self.inventory_dir = Path(JSON_INVENTORY_PATH)
        self.inventory_dir.mkdir(exist_ok=True)

    def account_store(self, email):
        return AccountJSONStore(email)

    def load_all(self):
        """Load all JSON files into global cache."""
        for file_path in self.inventory_dir.glob("*.json"):
            if (
                file_path.suffix != ".json"
                or file_path.stem == 'items_cache'
                or file_path.stem == 'weapon_modifier_cache'
            ):
                continue
            email = file_path.stem
            AccountJSONStore(email).load()

        return TEAM_INVENTORY_CACHE

    def clear_all_data(self):
        """Delete all JSON files and clear cache."""
        TEAM_INVENTORY_CACHE.clear()
        for file_path in self.inventory_dir.glob("*.json"):
            try:
                file_path.unlink()
                backup_path = file_path.with_suffix(".json.bak")
                if backup_path.exists():
                    backup_path.unlink()
            except Exception as e:
                ConsoleLog("MultiAccountInventoryStore", f"[WARN] Failed to delete {file_path}: {e}")


multi_store = MultiAccountInventoryStore()
inventory_model_ids_store = ModelIDJSONStore()
inventory_mod_hash_store = ModHashJSONStore()


# region Generators
def get_character_bag_items_coroutine(bag, bag_id, email, char_name, bag_name):
    """Updates recorded_data[email]["Characters"][char_name]["Inventory"][bag_name]"""

    store = AccountJSONStore(email)
    if not email or not char_name:
        return

    bag_items = yield from _collect_bag_items(bag, bag_id, email, char_name=char_name)
    store.save_bag(char_name=char_name, bag_name=bag_name, bag_items=bag_items)


def get_storage_bag_items_coroutine(bag, bag_id, email, storage_name):
    """Updates recorded_data[email]["Storage"][bag_name]"""

    store = AccountJSONStore(email)
    if not email:
        return

    bag_items = yield from _collect_bag_items(bag, bag_id, email, storage_name=storage_name)
    store.save_bag(storage_name=storage_name, bag_items=bag_items)


def _collect_bag_items(bag, bag_id, email, storage_name=None, char_name=None):
    global current_character_name
    global multi_store

    """Shared coroutine to fetch all items from a bag with modifier and Frenkey DB name support."""

    def _strip_markup(text):
        if not text:
            return ""

        text = re.sub(r"<c=[^>]+>(.*?)</c>", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\{s\}", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\{sc\}", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</?p>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\{[^}]+\}", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s+", "\n", text)

        return text.strip()

    def _find_last_name_stored_model_id(model_id, slot, count, storage_name=None, char_name=None):
        if char_name:
            items = (
                TEAM_INVENTORY_CACHE.get(email, {})
                .get("Characters", {})
                .get(char_name, {})
                .get("Inventory", {})
                .get(Bags(bag_id).name, {})
            )
        elif storage_name:
            items = TEAM_INVENTORY_CACHE.get(email, {}).get("Storage", {}).get(storage_name, {})
        else:
            items = {}

        for item_name, value in items.items():
            if value.get("model_id") == model_id and value.get("slot", {}).get(str(slot), 0) == count:
                return item_name

        return None

    def _generate_unique_key(bag_items: dict, base_name: str) -> str:
        if base_name not in bag_items:
            return base_name

        i = 1
        while f"{base_name} #{i}" in bag_items:
            i += 1

        return f"{base_name} #{i}"

    def _get_frenkey_texture_file(model_id, item_type):
        if LOOTEX_AVAILABLE and Data:
            data = Data()
            item_data = data.Items[item_type].get(model_id)
            if item_data:
                return item_data.texture_file
        return ''

    bag_items = OrderedDict()

    for item in bag.GetItems():
        if not item or item.model_id == 0:
            continue

        model_id = item.model_id
        item_id = item.item_id
        quantity = item.quantity
        slot = item.slot
        item_type = item.item_type.ToInt()

        final_name = None

        # Try LootEx, will fail if model id data isn't there
        if GLOBAL_CACHE.Item.Type.IsWeapon(item_id) and not GLOBAL_CACHE.Item.Rarity.IsGreen(item_id):
            final_name = get_weapon_name_from_modifiers(item)
        elif GLOBAL_CACHE.Item.Type.IsArmor(item_id):
            final_name = get_armor_name_from_modifiers(item)

        # For generic items, we use Model ID
        if not final_name:
            try:
                final_name = ModelID(model_id).name.replace("_", " ")

                # Special dye handling - maybe need to hadle mods and whatever here too
                if model_id == ModelID.Vial_Of_Dye:
                    dye_int = GLOBAL_CACHE.Item.GetDyeColor(item_id)
                    final_name = f"{final_name} [{DyeColor(dye_int).name}]"
            except ValueError:
                final_name = None

        # Fetch from last state of the account
        if not final_name:
            stored_name = _find_last_name_stored_model_id(
                model_id, slot, quantity, storage_name=storage_name, char_name=char_name
            )
            if stored_name:
                final_name = stored_name

        if not final_name:
            try:
                markedup = yield from Routines.Yield.Items.GetItemNameByItemID(item_id)
                final_name = _strip_markup(markedup)
                if final_name:
                    model_name, prefix, suffix = clean_gw_item_name(final_name)
                    inventory_model_ids_store.save_model_id(model_id, model_name)
                    mod_hash = ModHashJSONStore.hash_mods(item.modifiers)
                    inventory_mod_hash_store.save_mod_hash(mod_hash, prefix, suffix)

            except Exception as e:
                print(f"Exception fetching name for {item_id}: {e}")
                final_name = None

        # Nothing worked → cannot name item
        if not final_name:
            continue

        unique_name = final_name
        if final_name in bag_items:
            unique_name = _generate_unique_key(bag_items, final_name)

        # Always insert or update using the unique name
        if unique_name not in bag_items:
            bag_items[unique_name] = OrderedDict(
                {
                    "model_id": model_id,
                    "slot": OrderedDict(),
                    "lootex_texture_file": _get_frenkey_texture_file(model_id, item_type),
                }
            )

        bag_items[unique_name]["slot"][str(slot)] = quantity

    return bag_items


def record_account_data():
    global current_character_name

    current_email = Player.GetAccountEmail()
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
    char_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)

    if not current_email or not char_name:
        yield
        return

    current_character_name = char_name
    raw_item_cache = GLOBAL_CACHE.Inventory._raw_item_cache

    for bag_name, bag_id in INVENTORY_BAGS.items():
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from (
            get_character_bag_items_coroutine(
                bag,
                bag_id,
                current_email,
                char_name=char_name,
                bag_name=bag_name,
            )
        )

    for storage_name, bag_id in STORAGE_BAGS.items():
        if bag_id is None:
            continue
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from (
            get_storage_bag_items_coroutine(
                bag,
                bag_id,
                current_email,
                storage_name=storage_name,
            )
        )


# region Helper functions
def search(query: str, items: list[str]) -> list[str]:
    """Return items matching partially or with fuzzy similarity."""
    if not query:
        return items

    query = query.lower()

    # --- Partial match first (fast) ---
    partial_matches = [item for item in items if query in item.lower()]

    return sorted(partial_matches)


def get_armor_name_from_modifiers(item):
    if not LOOTEX_AVAILABLE or not Util:
        try:
            base_name = ModelID(item.model_id).name.replace("_", " ")
        except ValueError:
            base_name = None

        base_name = INVENTORY_MODEL_ID_CACHE.get(str(item.model_id))
        if not base_name:
            return None

        if base_name:
            mod_hash = ModHashJSONStore.hash_mods(item.modifiers)
            if mod_hash not in INVENTORY_MOD_HASH_CACHE:
                return None

            prefix, suffix = INVENTORY_MOD_HASH_CACHE.get(mod_hash, [None, None])

            name_parts = []

            if prefix:
                name_parts.append(prefix)

            name_parts.append(base_name)

            if suffix:
                name_parts.append(suffix)

            return " ".join(name_parts)
        return None

    # Prefer the in-game name if available
    final_name = Util.GetItemDataName(item.item_id)
    if final_name and not final_name.startswith("Unknown"):
        base_name, _prefix, _suffix = clean_gw_item_name(final_name)
        base_name = base_name.strip()
    else:
        try:
            base_name = ModelID(item.model_id).name.replace("_", " ")
        except ValueError:
            base_name = None

        if not base_name:
            base_name = INVENTORY_MODEL_ID_CACHE.get(str(item.model_id))

        if not base_name:
            return None

    # Collect mods
    _, armor_mods, _ = Util.GetMods(item.item_id)
    prefix = None
    suffix = None

    for armor_mod in armor_mods:
        mod_name = armor_mod.identifier.strip()
        mod_type = armor_mod.mod_type.name

        if mod_type == "Prefix":
            prefix = mod_name
        elif mod_type == "Suffix":
            suffix = mod_name

    # --- Construct name ---
    name_parts = []

    name_parts.append(base_name)

    if prefix:
        name_parts.append(f'| {prefix}')

    if suffix:
        name_parts.append(f"| {suffix}")

    return " ".join(name_parts)


def get_weapon_name_from_modifiers(item):
    if not LOOTEX_AVAILABLE or not Util:
        try:
            base_name = ModelID(item.model_id).name.replace("_", " ")
        except ValueError:
            base_name = None

        base_name = INVENTORY_MODEL_ID_CACHE.get(str(item.model_id))
        if not base_name:
            return None

        if base_name:
            mod_hash = ModHashJSONStore.hash_mods(item.modifiers)
            if mod_hash not in INVENTORY_MOD_HASH_CACHE:
                return None

            prefix, suffix = INVENTORY_MOD_HASH_CACHE.get(mod_hash, [None, None])

            name_parts = []
            # Inherent mods like “Vampiric” or “Insightful” go before everything else
            if prefix:
                name_parts.append(prefix)

            name_parts.append(base_name)

            if suffix:
                name_parts.append(f"{suffix}")

            return " ".join(name_parts)
        return None

    # Prefer the in-game name if available
    final_name = Util.GetItemDataName(item.item_id)
    if final_name and not final_name.startswith("Unknown"):
        base_name, _prefix, _suffix = clean_gw_item_name(final_name)
        base_name = base_name.strip()
    else:
        base_name = None

    if not base_name:
        base_name = INVENTORY_MODEL_ID_CACHE.get(str(item.model_id))

    if not base_name:
        return None

    # Collect mods
    _, _, weapon_mods = Util.GetMods(item.item_id)
    prefix = None
    suffix = None
    inherent = None

    for weapon_mod in weapon_mods:
        mod_name = weapon_mod.identifier.strip()
        mod_type = weapon_mod.mod_type.name

        if mod_type == "Prefix":
            prefix = mod_name
        elif mod_type == "Suffix":
            suffix = mod_name
        elif mod_type == "Inherent":
            inherent = mod_name

    # --- Construct name ---
    name_parts = []

    # Inherent mods like “Vampiric” or “Insightful” go before everything else
    if prefix:
        name_parts.append(prefix)

    name_parts.append(base_name)

    if suffix:
        name_parts.append(f"{suffix}")

    if inherent:
        name_parts.append(f"({inherent})")

    return " ".join(name_parts)


# region Widget
def draw_widget():
    global TEAM_INVENTORY_CACHE
    global INVENTORY_MODEL_ID_CACHE
    global INVENTORY_MOD_HASH_CACHE
    global window_x
    global window_y
    global window_collapsed
    global first_run
    global all_accounts_search_query
    global search_query
    global on_first_load
    global current_character_name
    global multi_store
    global inventory_model_ids_store
    global inventory_mod_hash_store

    if on_first_load:
        PyImGui.set_next_window_size(1000, 1250)
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        on_first_load = False
        if LOOTEX_AVAILABLE:
            Data().Load()  # type: ignore

        TEAM_INVENTORY_CACHE = multi_store.load_all()
        INVENTORY_MODEL_ID_CACHE = inventory_model_ids_store.load()
        INVENTORY_MOD_HASH_CACHE = inventory_mod_hash_store.load()

    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    # This triggers a reload of and save of bag data
    if inventory_write_timer.IsExpired() and Routines.Checks.Map.IsOutpost():
        GLOBAL_CACHE.Coroutines.append(record_account_data())
        inventory_write_timer.Reset()

    if inventory_read_timer.IsExpired() and Routines.Checks.Map.IsOutpost():
        TEAM_INVENTORY_CACHE = multi_store.load_all()
        inventory_read_timer.Reset()

    if PyImGui.begin("Team Inventory Viewer"):
        PyImGui.text("Inventory + Storage Viewer")
        PyImGui.separator()

        # === SCROLLABLE AREA START ===
        # Compute space for footer
        available_height = PyImGui.get_window_height() - 190  # leave room for buttons + footer
        PyImGui.begin_child("ScrollableContent", (0.0, float(available_height)), True, 1)

        # === TABS BY ACCOUNT ===
        if TEAM_INVENTORY_CACHE:
            if PyImGui.begin_tab_bar("AccountTabs"):
                # === GLOBAL SEARCH TAB ===
                if PyImGui.begin_tab_item("Search View"):
                    PyImGui.text("Search for items across all accounts")
                    PyImGui.separator()

                    all_accounts_search_query = PyImGui.input_text("##GlobalSearchBar", all_accounts_search_query, 128)
                    PyImGui.separator()

                    if all_accounts_search_query:
                        # === Gather all matching results across accounts ===
                        search_results = []
                        for email, account_data in TEAM_INVENTORY_CACHE.items():
                            # Build a neat identifier like: email — [Char1, Char2]
                            character_names = list(account_data.get("Characters", {}).keys())
                            if character_names:
                                character_block = "\n".join(f"   - {name}" for name in character_names)
                                account_label = f"{character_block}"
                            else:
                                account_label = "[No Characters]"

                            # --- Characters ---
                            if "Characters" in account_data:
                                for char_name, char_info in account_data["Characters"].items():
                                    inv_data = char_info.get("Inventory", {})
                                    for bag_name, items in inv_data.items():
                                        for item_name, info in items.items():
                                            if all_accounts_search_query.lower() in item_name.lower():
                                                count = 0
                                                for slot_count in info.get("slot", {}).values():
                                                    count += slot_count
                                                search_results.append(
                                                    {
                                                        "account_label": account_label,
                                                        "email": email,
                                                        "character": char_name,
                                                        "bag": bag_name,
                                                        "item_name": item_name,
                                                        "model_id": info["model_id"],
                                                        "lootex_texture_file": info.get("lootex_texture_file"),
                                                        "count": count or str(info.get('count', 0)),
                                                        "location_type": "Character",
                                                    }
                                                )

                            # --- Storage ---
                            if "Storage" in account_data:
                                for storage_name, items in account_data["Storage"].items():
                                    for item_name, info in items.items():
                                        if all_accounts_search_query.lower() in item_name.lower():
                                            count = 0
                                            for slot_count in info.get("slot", {}).values():
                                                count += slot_count
                                            search_results.append(
                                                {
                                                    "account_label": account_label,
                                                    "email": email,
                                                    "character": None,
                                                    "bag": storage_name,
                                                    "item_name": item_name,
                                                    "model_id": info["model_id"],
                                                    "lootex_texture_file": info.get("lootex_texture_file"),
                                                    "count": count or str(info.get('count', 0)),
                                                    "location_type": "Storage",
                                                }
                                            )

                        # === Display results ===
                        if search_results:
                            # Sort alphabetically ignoring leading numbers
                            search_results.sort(key=lambda entry: re.sub(r'^\d+\s*', '', entry["item_name"]).lower())
                            if PyImGui.begin_table(
                                "SearchResultsTable",
                                5,
                                PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY,
                            ):
                                PyImGui.table_setup_column("Icon", 0, 30.0)
                                PyImGui.table_setup_column("Item Name", 0, 300.0)
                                PyImGui.table_setup_column("Count", 0, 50.0)
                                PyImGui.table_setup_column("Location", 0, 150.0)
                                PyImGui.table_setup_column("Account", 0, 150.0)
                                PyImGui.table_headers_row()

                                for index, entry in enumerate(search_results):
                                    texture = get_texture_for_model(entry["model_id"])

                                    if '0-File_Not_found' in texture:
                                        lootex_texture = entry.get('lootex_texture_file')
                                        if lootex_texture:
                                            texture = lootex_texture
                                    PyImGui.table_next_row()

                                    # === ICON ===
                                    PyImGui.table_next_column()
                                    if texture:
                                        ImGui.DrawTexture(texture, 20, 20)
                                    else:
                                        PyImGui.text("N/A")

                                    # === ITEM NAME ===
                                    PyImGui.table_next_column()
                                    PyImGui.text(re.sub(r'^\d+\s*', '', entry["item_name"]))

                                    # === COUNT ===
                                    PyImGui.table_next_column()
                                    count = 0
                                    for slot_count in entry.get("slot", {}).values():
                                        count += slot_count
                                    PyImGui.text(str(count) if count else str(entry.get('count', 0)))

                                    # === LOCATION ===
                                    PyImGui.table_next_column()
                                    if entry["location_type"] == "Character":
                                        PyImGui.text(f"{entry['character']}\n  - {entry['bag']}")
                                    else:
                                        PyImGui.text(f"Storage\n  - {entry['bag']}")

                                    # === ACCOUNT IDENTIFIER ===
                                    PyImGui.table_next_column()
                                    if PyImGui.collapsing_header(f'{entry["email"]}##{index}'):
                                        PyImGui.text(entry["account_label"])

                                PyImGui.end_table()
                        else:
                            PyImGui.text("No matching items found.")
                    else:
                        PyImGui.text("Type above to search across all accounts.")
                    PyImGui.end_tab_item()
                for email, account_data in TEAM_INVENTORY_CACHE.items():
                    if PyImGui.begin_tab_item(email):
                        PyImGui.text(f"Account: {email}")
                        PyImGui.separator()

                        # === SEARCH BAR ===
                        PyImGui.text("Search Items:")
                        search_query = PyImGui.input_text("##SearchBar", search_query, 128)
                        PyImGui.separator()

                        PyImGui.begin_child(f"Child_{email}")

                        # === CHARACTER INVENTORIES ===
                        if "Characters" in account_data:
                            for char_name, char_info in account_data["Characters"].items():
                                if char_name == "Invalid ID":
                                    continue

                                if PyImGui.collapsing_header(char_name, True):
                                    inv_data = char_info.get("Inventory", {})
                                    ordered_inv_data = {
                                        bag_name: inv_data.get(bag_name, [])
                                        for bag_name in INVENTORY_BAGS.keys()
                                        if bag_name in inv_data
                                    }
                                    for bag_name, items in ordered_inv_data.items():
                                        if not items:
                                            continue

                                        # Filter visible items
                                        item_names = list(items.keys())
                                        filtered_items = item_names
                                        if search_query:
                                            filtered_items = search(search_query, item_names)
                                        if not filtered_items:
                                            continue

                                        PyImGui.text(bag_name)
                                        if PyImGui.begin_table(
                                            f"InvTable_{email}_{char_name}_{bag_name}",
                                            3,
                                            PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg,
                                        ):
                                            PyImGui.table_setup_column("Icon", 0, 30.0)
                                            PyImGui.table_setup_column("Item Name", 0, 300.0)
                                            PyImGui.table_setup_column("Count", 0, 25.0)
                                            PyImGui.table_headers_row()

                                            for item_name in filtered_items:
                                                info = items[item_name]
                                                texture = get_texture_for_model(info["model_id"])

                                                if '0-File_Not_found' in texture:
                                                    lootex_texture = info.get('lootex_texture_file')
                                                    if lootex_texture:
                                                        texture = lootex_texture

                                                PyImGui.table_next_row()

                                                # === ICON COLUMN ===
                                                PyImGui.table_next_column()
                                                if texture:
                                                    ImGui.DrawTexture(texture, 20, 20)
                                                else:
                                                    PyImGui.text("N/A")

                                                # === ITEM NAME COLUMN ===
                                                PyImGui.table_next_column()
                                                PyImGui.text(re.sub(r'^\d+\s*', '', item_name))

                                                # === COUNT COLUMN ===
                                                PyImGui.table_next_column()
                                                count = 0
                                                for slot_count in info.get("slot", {}).values():
                                                    count += slot_count
                                                PyImGui.text(str(count) if count else str(info.get('count', 0)))
                                            PyImGui.end_table()
                                        PyImGui.separator()

                        # === STORAGE SECTION ===
                        if "Storage" in account_data:
                            if PyImGui.collapsing_header("Shared Storage", True):
                                account_storage = account_data.get("Storage", {})
                                ordered_storage_data = {
                                    storage_name: account_storage.get(storage_name, [])
                                    for storage_name in STORAGE_BAGS.keys()
                                    if storage_name in account_storage
                                }
                                for storage_name, items in ordered_storage_data.items():
                                    if not items:
                                        continue

                                    item_names = list(items.keys())
                                    filtered_items = item_names
                                    if search_query:
                                        filtered_items = search(search_query, item_names)
                                    if not filtered_items:
                                        continue

                                    PyImGui.text(storage_name)
                                    if PyImGui.begin_table(
                                        f"StorageTable_{email}_{storage_name}",
                                        3,
                                        PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg,
                                    ):
                                        PyImGui.table_setup_column("Icon", 0, 30.0)
                                        PyImGui.table_setup_column("Item Name", 0, 300.0)
                                        PyImGui.table_setup_column("Count", 0, 25.0)
                                        PyImGui.table_headers_row()

                                        for item_name in filtered_items:
                                            info = items[item_name]
                                            texture = get_texture_for_model(info["model_id"])

                                            if '0-File_Not_found' in texture:
                                                lootex_texture = info.get('lootex_texture_file')
                                                if lootex_texture:
                                                    texture = lootex_texture

                                            PyImGui.table_next_row()

                                            # === ICON COLUMN ===
                                            PyImGui.table_next_column()
                                            if texture:
                                                ImGui.DrawTexture(texture, 20, 20)
                                            else:
                                                PyImGui.text("N/A")

                                            # === ITEM NAME COLUMN ===
                                            PyImGui.table_next_column()
                                            PyImGui.text(re.sub(r'^\d+\s*', '', item_name))

                                            # === COUNT COLUMN ===
                                            PyImGui.table_next_column()
                                            count = 0
                                            for slot_count in info.get("slot", {}).values():
                                                count += slot_count
                                            PyImGui.text(str(count) if count else str(info.get('count', 0)))
                                        PyImGui.end_table()
                                    PyImGui.separator()

                        PyImGui.end_child()
                        PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        else:
            PyImGui.text("No recorded accounts found yet.")
        PyImGui.end_child()  # End scrollable section

        PyImGui.separator()
        current_character = f'Current Character: {current_character_name}'
        PyImGui.text(f"{"Waiting for ..." if not current_character_name else current_character}")
        if PyImGui.collapsing_header("Advanced Clearing", True):
            PyImGui.text(
                f'Save timer: {(inventory_write_timer.GetTimeRemaining() / 1000):.1f}(s), Read timer: {(inventory_read_timer.GetTimeRemaining() / 1000):.1f}(s)'
            )
            if PyImGui.begin_table("clear_buttons_table", 3, PyImGui.TableFlags.BordersInnerV):
                # Define colors
                orange_color = Color(255, 165, 0, 255).to_tuple_normalized()  # orange
                orange_hover = Color(255, 200, 50, 255).to_tuple_normalized()
                orange_active = Color(255, 140, 0, 255).to_tuple_normalized()

                red_color = Color(220, 20, 60, 255).to_tuple_normalized()  # crimson red
                red_hover = Color(255, 50, 80, 255).to_tuple_normalized()
                red_active = Color(180, 0, 40, 255).to_tuple_normalized()

                green_color = Color(50, 205, 50, 255).to_tuple_normalized()  # lime green
                green_hover = Color(80, 230, 80, 255).to_tuple_normalized()
                green_active = Color(0, 180, 0, 255).to_tuple_normalized()

                PyImGui.table_next_row()
                # === CLEAR CHARACTER ===
                PyImGui.table_set_column_index(0)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, green_active)
                if PyImGui.button("Clear Character", width=col_width):
                    current_email = Player.GetAccountEmail()
                    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(Player.GetAgentID())
                    char_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                    if current_email and char_name:
                        store = AccountJSONStore(current_email)
                        store.clear_character(char_name)
                    else:
                        ConsoleLog("Inventory Recorder", "No data found for this character.")
                PyImGui.pop_style_color(3)

                # === CLEAR CURRENT ACCOUNT ===
                PyImGui.table_set_column_index(1)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, orange_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, orange_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, orange_active)
                if PyImGui.button("Clear Current account", width=col_width):
                    current_email = Player.GetAccountEmail()
                    if current_email:
                        store = AccountJSONStore(current_email)
                        store.clear_account()
                        TEAM_INVENTORY_CACHE = multi_store.load_all()
                    else:
                        ConsoleLog("Inventory Recorder", "No data found for this account.")
                PyImGui.pop_style_color(3)

                # === CLEAR ALL ACCOUNTS ===
                PyImGui.table_set_column_index(2)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, red_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, red_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, red_active)
                if PyImGui.button("Clear all accounts", width=col_width):
                    multi_store.clear_all_data()
                    TEAM_INVENTORY_CACHE = multi_store.load_all()
                PyImGui.pop_style_color(3)
                PyImGui.end_table()

    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))
        # Collapsed state changed?
        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))
        save_window_timer.Reset()


def configure():
    pass


def json_tree_view(data):
    # Convert JSON to pretty string
    json_str = json.dumps(data, indent=2)

    # --- In your PyImGui render loop ---
    PyImGui.begin("JSON Viewer", True)

    # Display the JSON string
    PyImGui.text_unformatted(json_str)

    PyImGui.end_child()
    PyImGui.end()


def main():
    try:
        if not Routines.Checks.Map.MapValid() or Map.Pregame.InCharacterSelectScreen():
            # When swapping characters, reset everything
            return

        if Routines.Checks.Map.IsMapReady():
            draw_widget()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
