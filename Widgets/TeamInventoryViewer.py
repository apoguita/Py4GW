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
from Py4GWCoreLib import get_texture_for_model
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums import ModelID


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
    global ITEM_ID_CACHE
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

    bag_items = OrderedDict()

    for item in bag.GetItems():
        if not item or item.model_id == 0:
            continue

        model_id = item.model_id
        item_id = item.item_id
        quantity = item.quantity
        slot = item.slot

        try:
            final_name = ModelID(model_id).name.replace("_", " ")

            # Special dye handling - maybe need to hadle mods and whatever here too
            if model_id == ModelID.Vial_Of_Dye:
                dye_int = GLOBAL_CACHE.Item.GetDyeColor(item_id)
                final_name = f"{final_name} [{DyeColor(dye_int).name}]"
        except ValueError:
            final_name = None

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
            except Exception as e:
                print(f"Exception fetching name for {item_id}: {e}")
                final_name = None

        # Nothing worked → cannot name item
        if not final_name:
            continue

        if final_name in bag_items:
            final_name = _generate_unique_key(bag_items, final_name)

        if final_name not in bag_items:
            bag_items[final_name] = OrderedDict({
                "model_id": model_id,
                "slot": OrderedDict({str(slot): quantity}),
            })
        else:
            bag_items[final_name]["slot"][str(slot)] = quantity

    return bag_items


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
    global ITEM_ID_CACHE
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
        TEAM_INVENTORY_CACHE = multi_store.load_all()
        ITEM_ID_CACHE = {}

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


def json_tree_view_debug(data):
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
        if (
            not Routines.Checks.Map.MapValid()
            or GLOBAL_CACHE.Player.InCharacterSelectScreen()
            or not Routines.Checks.Map.IsOutpost()
        ):
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
