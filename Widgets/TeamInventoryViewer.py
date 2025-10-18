import json
import os
import re
import shutil
import traceback
import urllib.request
from collections import OrderedDict
from pathlib import Path

import Py4GW  # type: ignore
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Color
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib import get_texture_for_model
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums import ModelID
from Py4GWCoreLib.enums import ItemType


script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))


BASE_DIR = os.path.join(project_root, "Widgets/Config")
DB_BASE_DIR = os.path.join(project_root, "Widgets/Data")
JSON_INVENTORY_PATH = os.path.join(DB_BASE_DIR, "Inventory")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "team_inventory_viewer.ini")
os.makedirs(BASE_DIR, exist_ok=True)

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()
inventory_write_timer = ThrottledTimer(3000)
inventory_read_timer = ThrottledTimer(5000)

# String consts
MODULE_NAME = "TeamInventoryViewer"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

# View data
first_run = True
on_first_load = True
all_accounts_search_query = ''
search_query = ''
current_character_name = ''

TEAM_INVENTORY_CACHE = {}
WEAPON_MODIFIER_DB = {}
WEAPON_MODIFIER_LOOKUP = {}
WEAPON_MODIFIER_DB_PATH = os.path.join(JSON_INVENTORY_PATH, "weapon_modifier_cache.json")
WEAPON_MODIFIER_DB_URL = 'https://raw.githubusercontent.com/frenkey-derp/Py4GW/refs/heads/live_dev_lootex/Widgets/frenkey/LootEx/data/weapon_mods.json'
ITEM_NAME_DB = {}
ITEM_NAME_DB_PATH = os.path.join(JSON_INVENTORY_PATH, "items_cache.json")
ITEM_NAME_DB_URL = "https://raw.githubusercontent.com/frenkey-derp/Py4GW/refs/heads/live_dev_lootex/Widgets/frenkey/LootEx/data/items.json"

INVENTORY_BAGS = {
    "Backpack": Bags.Backpack.value,
    "BeltPouch": Bags.BeltPouch.value,
    "Bag1": Bags.Bag1.value,
    "Bag2": Bags.Bag2.value,
    "EquipmentPack": Bags.EquipmentPack.value,
    "Equipped": Bags.EquippedItems.value,
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

TARGET_WEAPON_TYPES = {
    "Weapon": [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Staff,
        ItemType.Sword,
        ItemType.Wand
    ],

    "MartialWeapon": [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Sword
    ],

    "OffhandOrShield": [
        ItemType.Offhand,
        ItemType.Shield
    ],

    "EquippableItem": [
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
        ItemType.Wand
    ],

    "SpellcastingWeapon": [
        ItemType.Offhand,
        ItemType.Staff,
        ItemType.Wand
    ],
}


# region JSONStore
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

    # --- Cached interface ---
    def load(self):
        if self.email in TEAM_INVENTORY_CACHE:
            return TEAM_INVENTORY_CACHE[self.email]

        data = self._read()
        TEAM_INVENTORY_CACHE[self.email] = data
        return data

    def save_to_disk(self):
        if self.email not in TEAM_INVENTORY_CACHE:
            return
        self._write(TEAM_INVENTORY_CACHE[self.email])

    def save_bag(self, char_name=None, storage_name=None, bag_name=None, bag_items={}):
        data = self._read()
        changed = False

        if char_name:
            chars = data["Characters"]
            if char_name not in chars:
                chars[char_name] = {"Inventory": OrderedDict()}
            inv = chars[char_name]["Inventory"]
            if inv.get(bag_name) != bag_items:
                inv[bag_name] = bag_items
                changed = True
        elif storage_name:
            storage = data["Storage"]
            if storage.get(storage_name) != bag_items:
                storage[storage_name] = bag_items
                changed = True

        if changed:
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
        except Exception as e:
            ConsoleLog("AccountJSONStore", f"[ERROR] clear_character: {e}")

    def clear_account(self):
        try:
            if self.file_path.exists():
                self.file_path.unlink()
            if self.backup_path.exists():
                self.backup_path.unlink()

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
            if file_path.suffix != ".json" or file_path.stem == 'items_cache' or file_path.stem == 'weapon_modifier_cache':
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
# inventory = Inventory()


# region Generators
def get_character_bag_items_coroutine(bag, email, char_name, bag_name):
    """Updates recorded_data[email]["Characters"][char_name]["Inventory"][bag_name]"""

    store = AccountJSONStore(email)
    if not email or not char_name:
        return

    bag_items = yield from _collect_bag_items(bag)
    store.save_bag(char_name=char_name, bag_name=bag_name, bag_items=bag_items)


def get_storage_bag_items_coroutine(bag, email, storage_name):
    """Updates recorded_data[email]["Storage"][bag_name]"""

    store = AccountJSONStore(email)
    if not email:
        return

    bag_items = yield from _collect_bag_items(bag)
    store.save_bag(storage_name=storage_name, bag_items=bag_items)


def _collect_bag_items(bag):
    """Shared coroutine to fetch all items from a bag with modifier and Frenkey DB name support."""
    bag_items = OrderedDict()

    # Ensure JSON databases are loaded
    if not ITEM_NAME_DB:
        load_item_name_json()
    if not WEAPON_MODIFIER_DB:
        load_item_mods_json()

    for item in bag.GetItems():
        if not item or item.model_id == 0:
            continue

        model_id = item.model_id
        item_id = item.item_id
        quantity = item.quantity

        if GLOBAL_CACHE.Item.Type.IsWeapon(item_id):
            final_name = get_weapon_name_from_modifiers(item)
        else:
            try:
                final_name = ModelID(model_id).name.replace("_", " ")
            except ValueError:
                final_name = None

        # === 4️⃣ Fallback to in-game request ===
        if not final_name:
            try:
                if not GLOBAL_CACHE.Item.IsNameReady(item_id):
                    GLOBAL_CACHE.Item.RequestName(item_id)
                    yield from Routines.Yield.wait(200)

                if GLOBAL_CACHE.Item.IsNameReady(item_id):
                    final_name = GLOBAL_CACHE.Item.GetName(item_id)
            except Exception as e:
                print(f"Exception fetching name for {item_id}: {e}")
                final_name = None

        if not final_name:
            continue

        # === Record result ===
        if final_name not in bag_items:
            bag_items[final_name] = {"model_id": model_id, "count": quantity}
        else:
            bag_items[final_name]["count"] += quantity

    return bag_items


def get_weapon_name_from_modifiers(item):
    """
    Build a readable weapon name using only item.modifiers and WEAPON_MODIFIER_DB.
    Returns: "Prefix BaseName Suffix (Inherent)" style name
    """
    def get_item_meta_keys(item_name: str) -> set[str]:
        keys = set()
        for meta_key, types in TARGET_WEAPON_TYPES.items():
            if any(t.name == item_name for t in types):
                keys.add(meta_key)
        return keys
    
    # Step 1: Base name
    base_name = str(item.item_type.GetName())

    # Step 2: Convert item modifiers to tuples
    modifier_values = [
        (mod.GetIdentifier(), mod.GetArg(), mod.GetArg1(), mod.GetArg2())
        for mod in item.modifiers if mod is not None
    ]

    prefix, suffix, inherent = None, None, None

    mod_targets = []
    # Step 3: Match item modifiers to weapon DB
    for mod_id, arg, arg1, arg2 in modifier_values:
        for mod_name, mod_data in WEAPON_MODIFIER_DB.items():
            for m in mod_data.get("Modifiers", []):
                # Skip the "ModifierValueArg" for lookup
                value_arg = m.get("ModifierValueArg")
                mod_targets = mod_data.get("TargetTypes", [])
                args_to_check = {
                    "Arg": m.get("Arg", 0),
                    "Arg1": m.get("Arg1", 0),
                    "Arg2": m.get("Arg2", 0),
                }
                if value_arg in args_to_check:
                    args_to_check[value_arg] = None  # ignore value arg


                # Only match if Identifier matches
                if m["Identifier"] != mod_id:
                    continue

                # Check if all other args match
                match = True
                for k, v in args_to_check.items():
                    if v is None:
                        continue
                    if k == "Arg" and v != arg:
                        match = False
                        break
                    if k == "Arg1" and v != arg1:
                        match = False
                        break
                    if k == "Arg2" and v != arg2:
                        match = False
                        break
                if not match:
                    continue

                # If we reach here, we have a match
                mod_type = mod_data.get("ModType", "Inherent").lower()
                if mod_type == "prefix":
                    prefix = mod_name
                elif mod_type == "suffix":
                    suffix = mod_name
                elif mod_type == "inherent":
                    inherent = mod_name

    # Step 4: Construct final name
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(base_name)
    if suffix:
        parts.append(suffix)

    final_name = " ".join(parts)
    if inherent:
        final_name += f" ({inherent})"

    if 'Shield of Devotion' in final_name:
        print(mod_targets)
        print(item.item_type.GetName())

    return final_name

def load_item_name_json(force_refresh=False):
    """Load or refresh the item name database from GitHub (cached locally)."""
    global ITEM_NAME_DB

    # Load from local file if exists and not refreshing
    if not force_refresh and os.path.exists(ITEM_NAME_DB_PATH):
        try:
            with open(ITEM_NAME_DB_PATH, "r", encoding="utf-8") as f:
                ITEM_NAME_DB = json.load(f)
                return
        except Exception as e:
            print(f"[ItemNameDB] Failed to read cache: {e}")

    # Otherwise, download fresh copy
    try:
        print("[ItemNameDB] Downloading latest items.json...")
        with urllib.request.urlopen(ITEM_NAME_DB_URL, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            ITEM_NAME_DB = data
            with open(ITEM_NAME_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[ItemNameDB] Cached {len(data)} entries.")
    except Exception as e:
        print(f"[ItemNameDB] Failed to download: {e}")
        ITEM_NAME_DB = {}


def load_item_mods_json(force_refresh=False):
    """Load or refresh the weapon modifiers database from GitHub (cached locally)."""
    global WEAPON_MODIFIER_DB

    if not force_refresh and os.path.exists(WEAPON_MODIFIER_DB_PATH):
        try:
            with open(WEAPON_MODIFIER_DB_PATH, "r", encoding="utf-8") as f:
                WEAPON_MODIFIER_DB = json.load(f)
        except Exception as e:
            print(f"[ItemModsDB] Failed to read cache: {e}")
            WEAPON_MODIFIER_DB = {}

    if not WEAPON_MODIFIER_DB:
        try:
            print("[ItemModsDB] Downloading latest weapon_mods.json...")
            with urllib.request.urlopen(WEAPON_MODIFIER_DB_URL, timeout=10) as response:
                WEAPON_MODIFIER_DB = json.loads(response.read().decode("utf-8"))
            with open(WEAPON_MODIFIER_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(WEAPON_MODIFIER_DB, f, indent=2)
            print(f"[ItemModsDB] Cached {len(WEAPON_MODIFIER_DB)} entries.")
        except Exception as e:
            print(f"[ItemModsDB] Failed to download: {e}")
            WEAPON_MODIFIER_DB = {}


def record_account_data():
    global current_character_name

    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
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


def aggregate_items_by_model(items_dict):
    """
    Given a dict of items (item_name -> {"model_id", "count"}), return
    a dict of model_id -> {"name": first_item_name, "count": total_count}.
    """
    agg = OrderedDict()
    for name, info in items_dict.items():
        model_id = info["model_id"]
        count = info["count"]

        if model_id not in agg:
            agg[model_id] = {"name": name, "count": count}
        else:
            agg[model_id]["count"] += count
    return agg


# region Widget
def draw_widget():
    global TEAM_INVENTORY_CACHE
    global window_x
    global window_y
    global window_collapsed
    global first_run
    global all_accounts_search_query
    global search_query
    global on_first_load
    global current_character_name
    global multi_store

    if on_first_load:
        PyImGui.set_next_window_size(1000, 1000)
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        on_first_load = False
        # Load all accounts for search
        TEAM_INVENTORY_CACHE = multi_store.load_all()

    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    # This triggers a reload of and save of bag data
    if inventory_write_timer.IsExpired():
        GLOBAL_CACHE.Coroutines.append(record_account_data())
        inventory_write_timer.Reset()

    if inventory_read_timer.IsExpired():
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
                                                search_results.append(
                                                    {
                                                        "account_label": account_label,
                                                        "email": email,
                                                        "character": char_name,
                                                        "bag": bag_name,
                                                        "item_name": item_name,
                                                        "model_id": info["model_id"],
                                                        "count": info["count"],
                                                        "location_type": "Character",
                                                    }
                                                )

                            # --- Storage ---
                            if "Storage" in account_data:
                                for storage_name, items in account_data["Storage"].items():
                                    for item_name, info in items.items():
                                        if all_accounts_search_query.lower() in item_name.lower():
                                            search_results.append(
                                                {
                                                    "account_label": account_label,
                                                    "email": email,
                                                    "character": None,
                                                    "bag": storage_name,
                                                    "item_name": item_name,
                                                    "model_id": info["model_id"],
                                                    "count": info["count"],
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
                                    PyImGui.text(str(entry["count"]))

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
                                                PyImGui.text(str(info["count"]))
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
                                            PyImGui.text(str(info["count"]))
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
                    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
                    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
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
                    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
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


def main():
    try:
        if not Routines.Checks.Map.MapValid() or GLOBAL_CACHE.Player.InCharacterSelectScreen():
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
