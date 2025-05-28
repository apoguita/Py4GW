import os
import json
import time
from Py4GWCoreLib import *

import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta

# Use hidden root for file dialogs
tk_root = tk.Tk()
tk_root.withdraw()


# --- Globals ---
loot_filter_singleton = LootConfig()
loot_items = []
temp_model_id = 0
initialized = False
include_model_id_in_tooltip = False
show_white_list = False
show_filtered_loot_list = False
show_manual_editor = False
show_black_list = False
use_formula_based_nick = False

last_config_check_time = 0
last_config_timestamp = 0
last_rarity_timestamp = 0

script_directory = os.path.dirname(os.path.abspath(__file__))
# ——— Window Persistence Setup ———
ini_window = IniHandler(os.path.join(script_directory, "Config", "loot_window.ini"))
save_window_timer = Timer()
save_window_timer.Start()

# load last‐saved window state (fallback to 100,100 / un-collapsed)
win_x         = ini_window.read_int("Loot Manager", "x", 100)
win_y         = ini_window.read_int("Loot Manager", "y", 100)
win_collapsed = ini_window.read_bool("Loot Manager", "collapsed", False)
first_run     = True

# --- File paths setup ---
CONFIG_FILE = os.path.join(script_directory, "Config", "loot_config.json")
MODELID_DROP_DATA_FILE = os.path.join(script_directory, "Data", "modelid_drop_data.json")
RARITY_FILTER_DATA_FILE = os.path.join(script_directory, "Data", "rarity_filter_data.json")

# --- Nick cycle setup ---
NICK_CYCLES_FILE = os.path.join(script_directory, "Data", "Nick_cycles.json")
nick_cycles = []
weeks_future = 0

def load_nick_cycles():
    global nick_cycles
    if os.path.exists(NICK_CYCLES_FILE):
        try:
            with open(NICK_CYCLES_FILE, "r") as f:
                nick_cycles = json.load(f)
            print(f"[INFO] Loaded {len(nick_cycles)} entries from Nick_cycles.json")
        except Exception as e:
            print(f"[ERROR] Failed to load Nick_cycles.json: {e}")
    else:
        print("[ERROR] Nick_cycles.json not found")

# --- File Handling ---
def load_modelid_drop_data():
    if os.path.exists(MODELID_DROP_DATA_FILE):
        try:
            with open(MODELID_DROP_DATA_FILE, "r") as f:
                data = json.load(f)
            print(f"[INFO] Loaded {len(data)} entries from modelid_drop_data.json")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load modelid_drop_data.json: {str(e)}")
    else:
        print("[ERROR] modelid_drop_data.json not found")
    return []

def load_rarity_filter_data():
    if os.path.exists(RARITY_FILTER_DATA_FILE):
        try:
            with open(RARITY_FILTER_DATA_FILE, "r") as f:
                data = json.load(f)
            print("[INFO] Loaded rarity_filter_data.json")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load rarity_filter_data.json: {str(e)}")
    else:
        print("[ERROR] rarity_filter_data.json not found")
    return {}

def save_loot_config():
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(loot_items, f, indent=4)
        print("[INFO] Saved loot_config.json")
    except Exception as e:
        print(f"[ERROR] Failed to save loot_config.json: {str(e)}")

def save_rarity_filter_data():
    try:
        os.makedirs(os.path.dirname(RARITY_FILTER_DATA_FILE), exist_ok=True)
        with open(RARITY_FILTER_DATA_FILE, "w") as f:
            json.dump({
                "white": loot_filter_singleton.loot_whites,
                "blue": loot_filter_singleton.loot_blues,
                "purple": loot_filter_singleton.loot_purples,
                "gold": loot_filter_singleton.loot_golds,
                "green": loot_filter_singleton.loot_greens,
                "gold_coins": loot_filter_singleton.loot_gold_coins,   # ← NEW
            }, f, indent=4)
        print("[INFO] Saved rarity_filter_data.json")
    except Exception as e:
        print(f"[ERROR] Failed to save rarity_filter_data.json: {str(e)}")

def load_loot_config():
    """
    Merge saved user settings back onto the fresh catalog.
    """
    # 1) Read saved flags into a dict
    saved = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                for entry in json.load(f):
                    saved[entry["model_id"]] = entry
        except Exception as e:
            print(f"[ERROR] Failed to parse {CONFIG_FILE}: {e}")

    # 2) Clear the whitelist
    loot_filter_singleton.ClearWhitelist()

    # 3) Merge saved flags onto each catalog item
    for item in loot_items:
        key = item["model_id"]
        if key in saved:
            item["enabled"]       = saved[key].get("enabled", False)
            item["rarity_filter"] = saved[key].get("rarity_filter", False)
        else:
            item["enabled"]       = False
            item["rarity_filter"] = False

        # 4) Whitelist enabled items
        if item["enabled"]:
            mid = item["model_id"]
            if isinstance(mid, str) and mid.startswith("ModelID."):
                name = mid.split(".", 1)[1]
                if hasattr(ModelID, name):
                    mid = getattr(ModelID, name)
            loot_filter_singleton.AddToWhitelist(mid)

    # 5) Always keep gold coins if that toggle’s on
    if loot_filter_singleton.loot_gold_coins:
        loot_filter_singleton.AddToWhitelist(ModelID.Gold_Coins.value)

    # 🔥 Rebuild singleton whitelist
    loot_filter_singleton.ClearWhitelist()
    for item in loot_items:
        if item.get("enabled", False):
            model_id = item.get("model_id")
            if isinstance(model_id, str) and model_id.startswith("ModelID."):
                model_id_name = model_id.split("ModelID.")[1]
                if hasattr(ModelID, model_id_name):
                    model_id = getattr(ModelID, model_id_name)
            loot_filter_singleton.AddToWhitelist(model_id)

    # ——— KEEP GOLD COINS WHITELISTED ———
    if loot_filter_singleton.loot_gold_coins:
        # ensure you have ModelID.Gold_Coin in your enum
        loot_filter_singleton.AddToWhitelist(ModelID.Gold_Coins.value)

def load_rarity_filter_settings():
    rarity_data = load_rarity_filter_data()
    loot_filter_singleton.SetProperties(
        loot_whites=rarity_data.get("white", False),
        loot_blues=rarity_data.get("blue", False),
        loot_purples=rarity_data.get("purple", False),
        loot_golds=rarity_data.get("gold", False),
        loot_greens=rarity_data.get("green", False),
        loot_gold_coins=rarity_data.get("gold_coins", False)
    )

    # if the user wants gold coins, ensure they remain whitelisted
    if loot_filter_singleton.loot_gold_coins:
        loot_filter_singleton.AddToWhitelist(ModelID.Gold_Coins.value)

def save_loot_config_to(path: str):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        output = {
            "items": loot_items,
            "rarity": {
                "loot_whites": loot_filter_singleton.loot_whites,
                "loot_blues": loot_filter_singleton.loot_blues,
                "loot_purples": loot_filter_singleton.loot_purples,
                "loot_golds": loot_filter_singleton.loot_golds,
                "loot_greens": loot_filter_singleton.loot_greens,
                "loot_gold_coins": loot_filter_singleton.loot_gold_coins,
            }
        }
        with open(path, "w") as f:
            json.dump(output, f, indent=4)
        print(f"[INFO] Saved loot config to: {path}")
    except Exception as e:
        print(f"[ERROR] Failed to save custom loot config: {e}")

def load_loot_config_from(path: str):
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        return

    try:
        with open(path, "r") as f:
            raw = json.load(f)
            saved_items = {entry["model_id"]: entry for entry in raw.get("items", [])}
            rarity = raw.get("rarity", {})
    except Exception as e:
        print(f"[ERROR] Failed to load from {path}: {e}")
        return

    loot_filter_singleton.ClearWhitelist()

    for item in loot_items:
        key = item["model_id"]
        if key in saved_items:
            saved_entry = saved_items[key]
            item["enabled"] = saved_entry.get("enabled", False)
            item["rarity_filter"] = saved_entry.get("rarity_filter", False)
        else:
            # Leave new items disabled by default
            item["enabled"] = False
            item["rarity_filter"] = False

        if item["enabled"]:
            model_id = item["model_id"]
            if isinstance(model_id, str) and model_id.startswith("ModelID."):
                model_id_name = model_id.split("ModelID.")[1]
                if hasattr(ModelID, model_id_name):
                    model_id = getattr(ModelID, model_id_name)
            loot_filter_singleton.AddToWhitelist(model_id)

    # Apply saved rarity filters
    loot_filter_singleton.SetProperties(
        loot_whites=rarity.get("white", False),
        loot_blues=rarity.get("blue", False),
        loot_purples=rarity.get("purple", False),
        loot_golds=rarity.get("gold", False),
        loot_greens=rarity.get("green", False),
        loot_gold_coins=rarity.get("gold_coins", False),
    )

    # Persist changes to avoid core loop overwrite
    save_rarity_filter_data()
    save_loot_config()

# --- Setup ---
def setup():
    global initialized, loot_items, last_config_timestamp

    if not initialized:
        _raw_catalog = load_modelid_drop_data()
        loot_items = [
            {**entry, "enabled": False, "rarity_filter": False}
            for entry in _raw_catalog
        ]

        rarity_data = load_rarity_filter_data()
        loot_filter_singleton.SetProperties(
            loot_whites=rarity_data.get("white", False),
            loot_blues=rarity_data.get("blue", False),
            loot_purples=rarity_data.get("purple", False),
            loot_golds=rarity_data.get("gold", False),
            loot_greens=rarity_data.get("green", False)
        )

        load_loot_config()
        load_nick_cycles()
        if os.path.exists(CONFIG_FILE):
            last_config_timestamp = os.path.getmtime(CONFIG_FILE)
        initialized = True


# --- GUI Functions ---
def _format_model_id(mid: int) -> str:
    try:
        m = ModelID(mid)
        pretty = m.name.replace("_", " ")
    except ValueError:
        pretty = "Unknown Item"
    return f"{pretty} (ModelID: {mid})"

def get_current_nick_item_by_formula():
    if not nick_cycles:
        load_nick_cycles()

    base_date = datetime.strptime("4/21/25", "%m/%d/%y").date()  # Cycle base
    today = datetime.today().date()
    this_monday = today - timedelta(days=today.weekday())

    weeks_since_start = (this_monday - base_date).days // 7
    index = weeks_since_start % len(nick_cycles)

    try:
        return nick_cycles[index]
    except IndexError:
        return None

def DrawWindow():
    global include_model_id_in_tooltip, show_white_list, show_filtered_loot_list
    global show_manual_editor, show_black_list
    global win_x, win_y, win_collapsed, first_run
    global weeks_future
    if not Routines.Checks.Map.MapValid():
        return

    # 1) On first draw, restore last position & collapsed state
    if first_run:
        PyImGui.set_next_window_pos(win_x, win_y)
        PyImGui.set_next_window_collapsed(win_collapsed, 0)
        first_run = False

    # 2) Begin the window (returns False if collapsed)
    opened = PyImGui.begin("Loot Manager", PyImGui.WindowFlags.AlwaysAutoResize)

    # 3) Immediately grab the live collapse & position, even if collapsed
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos       = PyImGui.get_window_pos()

    if opened:
        # —— Debug Settings ——
        if PyImGui.tree_node("Debug Settings"):
            include_model_id_in_tooltip = PyImGui.checkbox(
                "Display ModelID In Hovered Text", include_model_id_in_tooltip
            )
            show_white_list         = PyImGui.checkbox("Display White List", show_white_list)
            show_black_list         = PyImGui.checkbox("Display Black List", show_black_list)
            show_filtered_loot_list = PyImGui.checkbox(
                "Display Filtered Loot List", show_filtered_loot_list
            )
            show_manual_editor      = PyImGui.checkbox(
                "Manual Loot Configuration", show_manual_editor
            )
            PyImGui.tree_pop()

        # ——— Save/Load Configs ———
        PyImGui.separator()
        PyImGui.text("Save/Load Configs")
        PyImGui.separator()

        # Save Button
        if PyImGui.button(f"{IconsFontAwesome5.ICON_SAVE} Save to File"):
            path = filedialog.asksaveasfilename(
                title="Save Loot Config",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")]
            )
            if path:
                save_loot_config_to(path)

        PyImGui.same_line(0, 10)

        # Load Button
        if PyImGui.button(f"{IconsFontAwesome5.ICON_FILE_UPLOAD} Load from File"):
            path = filedialog.askopenfilename(
                title="Load Loot Config",
                filetypes=[("JSON Files", "*.json")]
            )
            if path:
                load_loot_config_from(path)

        if PyImGui.tree_node("Common"):
            rw = loot_filter_singleton.loot_whites
            rb = loot_filter_singleton.loot_blues
            rp = loot_filter_singleton.loot_purples
            rg = loot_filter_singleton.loot_golds
            re = loot_filter_singleton.loot_greens
            gc = loot_filter_singleton.loot_gold_coins

            new_rw = PyImGui.checkbox("White Items", rw)
            new_rb = PyImGui.checkbox("Blue Items", rb)
            new_rp = PyImGui.checkbox("Purple Items", rp)
            new_rg = PyImGui.checkbox("Gold Items", rg)
            new_re = PyImGui.checkbox("Green Items", re)
            new_gc = PyImGui.checkbox("Gold Coins", gc)

            if (new_rw, new_rb, new_rp, new_rg, new_re, new_gc) != (rw, rb, rp, rg, re, gc):
                # Update all properties at once
                loot_filter_singleton.SetProperties(
                    loot_whites=new_rw,
                    loot_blues=new_rb,
                    loot_purples=new_rp,
                    loot_golds=new_rg,
                    loot_greens=new_re,
                    loot_gold_coins=new_gc
                )
                save_rarity_filter_data()

                # Sync gold coins with whitelist
                coin_mid = ModelID.Gold_Coins.value
                if new_gc:
                    loot_filter_singleton.AddToWhitelist(coin_mid)
                else:
                    loot_filter_singleton.RemoveFromWhitelist(coin_mid)
                save_loot_config()

            PyImGui.tree_pop()

        PyImGui.separator()
        PyImGui.text("Nick's Items")
        global use_formula_based_nick
        use_formula_based_nick = PyImGui.checkbox("Use Formula-Based Nick Rotation", use_formula_based_nick)

        if use_formula_based_nick:
            weeks_future = PyImGui.slider_int("Weeks Ahead", weeks_future, 0, 12)

            base_date = datetime.strptime("4/21/25", "%m/%d/%y").date()
            today = datetime.today().date()
            this_monday = today - timedelta(days=today.weekday())
            weeks_since_start = (this_monday - base_date).days // 7

            upcoming = []
            for i in range(weeks_future + 1):
                index = (weeks_since_start + i) % len(nick_cycles)
                entry = nick_cycles[index]
                week_dt = this_monday + timedelta(weeks=i)
                upcoming.append((week_dt, entry["Item"]))

            for week_dt, item_name in upcoming:
                PyImGui.text(f"{week_dt.isoformat()}: {item_name}")

            if PyImGui.button(f"{IconsFontAwesome5.ICON_SAVE} Add Nick Items"):
                for week_dt, item_name in upcoming:
                    for item in loot_items:
                        if item["name"] == item_name and not item["enabled"]:
                            item["enabled"] = True
                            model_id = item.get("model_id")
                            if isinstance(model_id, str) and model_id.startswith("ModelID."):
                                model_id_name = model_id.split("ModelID.")[1]
                                if hasattr(ModelID, model_id_name):
                                    model_id = getattr(ModelID, model_id_name)
                            loot_filter_singleton.AddToWhitelist(model_id)
                save_loot_config()
        else:
            weeks_future = PyImGui.slider_int("Weeks Ahead", weeks_future, 0, 12)
            today = datetime.today().date()
            current_mon = today - timedelta(days=today.weekday())
            max_date = current_mon + timedelta(weeks=weeks_future)

            filtered = []
            for entry in nick_cycles:
                week_str = entry.get("Week", "")
                try:
                    ed = datetime.strptime(week_str, "%m/%d/%y").date()
                except ValueError:
                    continue
                if current_mon <= ed <= max_date:
                    filtered.append((ed, entry.get("Item", "")))

            for ed, nm in filtered:
                PyImGui.text(f"{ed.isoformat()}: {nm}")

            if PyImGui.button(f"{IconsFontAwesome5.ICON_SAVE} Add Nick Items"):
                for ed, nm in filtered:
                    for item in loot_items:
                        if item["name"] == nm and not item["enabled"]:
                            item["enabled"] = True
                            model_id = item.get("model_id")
                            if isinstance(model_id, str) and model_id.startswith("ModelID."):
                                model_id_name = model_id.split("ModelID.")[1]
                                if hasattr(ModelID, model_id_name):
                                    model_id = getattr(ModelID, model_id_name)
                            loot_filter_singleton.AddToWhitelist(model_id)
                save_loot_config()

        # —— Single-item Whitelist/Blacklist ——
        PyImGui.separator()
        PyImGui.text("Single items - By ModelID")
        PyImGui.separator()

        grouped = {}
        for item in loot_items:
            group    = item.get("group", "Unknown")
            subgroup = item.get("subgroup") or "Default"
            grouped.setdefault(group, {}).setdefault(subgroup, []).append(item)

        for group_name, subgroups in grouped.items():
            if PyImGui.tree_node(group_name):
                for subgroup_name, items in subgroups.items():
                    if PyImGui.tree_node(subgroup_name):
                        for item in items:
                            new_val = PyImGui.checkbox(item["name"], item["enabled"])
                            if new_val != item["enabled"]:
                                item["enabled"] = new_val
                                save_loot_config()

                                model_id = item.get("model_id")
                                if isinstance(model_id, str) and model_id.startswith("ModelID."):
                                    model_id_name = model_id.split("ModelID.")[1]
                                    if hasattr(ModelID, model_id_name):
                                        model_id = getattr(ModelID, model_id_name)

                                if new_val:
                                    loot_filter_singleton.AddToWhitelist(model_id)
                                else:
                                    loot_filter_singleton.RemoveFromWhitelist(model_id)

                            if PyImGui.is_item_hovered() and "drop_info" in item:
                                tip = f"Dropped from: {item['drop_info']}"
                                if include_model_id_in_tooltip:
                                    member_name = item['model_id'].split('.', 1)[1]
                                    enum_member = ModelID[member_name]
                                    tip += f" | ModelID: {enum_member.value}"
                                PyImGui.set_tooltip(tip)

                        PyImGui.tree_pop()
                PyImGui.tree_pop()

    # 5) End the window (must be called even if collapsed)
    PyImGui.end()

    # 6) Once per second, persist any position or collapse changes
    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (win_x, win_y):
            win_x, win_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key("Loot Manager", "x", str(win_x))
            ini_window.write_key("Loot Manager", "y", str(win_y))
        # Collapsed state changed?
        if new_collapsed != win_collapsed:
            win_collapsed = new_collapsed
            ini_window.write_key("Loot Manager", "collapsed", str(win_collapsed))
        save_window_timer.Reset()

def DrawWhitelistViewer():
    if show_white_list:
        if PyImGui.begin("Whitelist Viewer", None, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.separator()
            PyImGui.text("Filtered By Rarity")
            PyImGui.separator()

            try:
                PyImGui.text(f"White: {loot_filter_singleton.loot_whites}")
                PyImGui.text(f"Blue: {loot_filter_singleton.loot_blues}")
                PyImGui.text(f"Purple: {loot_filter_singleton.loot_purples}")
                PyImGui.text(f"Gold: {loot_filter_singleton.loot_golds}")
                PyImGui.text(f"Green: {loot_filter_singleton.loot_greens}")
                PyImGui.text(f"Gold Coins: {loot_filter_singleton.loot_gold_coins}")
            except Exception as e:
                PyImGui.text(f"Error reading rarity settings: {str(e)}")

            PyImGui.separator()
            PyImGui.text("Filtered By ModelID")
            PyImGui.separator()

            # raw_whitelist is a list of ints
            for raw_mid in sorted(loot_filter_singleton.GetWhitelist()):
                PyImGui.text(_format_model_id(raw_mid))

    PyImGui.end()

def DrawBlacklistViewer():
    if not show_black_list:
        return
    if not PyImGui.begin("Blacklist Viewer", None, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text("Black listed Items")
    PyImGui.separator()

    for raw_mid in sorted(loot_filter_singleton.GetBlacklist()):
        PyImGui.text(_format_model_id(raw_mid))

    PyImGui.end()

def DrawFilteredLootList():
    if not show_filtered_loot_list:
        return
    if not PyImGui.begin("Filtered Loot Window", None, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text("Filtered Loot Items Nearby")
    PyImGui.separator()

    loot_array = loot_filter_singleton.GetfilteredLootArray()
    display_list: list[tuple[int, float]] = []

    for agent_id in loot_array:
        try:
            # get raw model-ID and distance
            item_data = Agent.GetItemAgent(agent_id)
            raw_mid   = Item.GetModelID(item_data.item_id)
            dist      = Utils.Distance(Player.GetAgentID, agent_id)

            display_list.append((raw_mid, dist))

        except Exception as e:
            # print errors immediately
            PyImGui.text(f"Error loading item ({agent_id}): {e}")

    # sort by distance, then render with our unified formatter
    display_list.sort(key=lambda x: x[1])
    for mid, dist in display_list:
        PyImGui.text(f"{_format_model_id(mid)} — {dist:.1f} units")

    PyImGui.end()

def DrawManualLootConfig():
    global temp_model_id

    if show_manual_editor:
        if PyImGui.begin("Manual Loot Config Window", None, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("Manual Loot Configuration")

            temp_model_id = PyImGui.input_int("Model ID", temp_model_id)

            PyImGui.separator()
            PyImGui.text("Whitelist Actions")

            if PyImGui.button("Add ModelID to Whitelist"):
                loot_filter_singleton.AddToWhitelist(temp_model_id)
                for item in loot_items:
                    if item.get("model_id") == temp_model_id:
                        item["enabled"] = True
                save_loot_config()
                temp_model_id = 0

            if PyImGui.button("Remove ModelID from Whitelist"):
                loot_filter_singleton.RemoveFromWhitelist(temp_model_id)
                for item in loot_items:
                    if item.get("model_id") == temp_model_id:
                        item["enabled"] = False
                save_loot_config()
                temp_model_id = 0

            if PyImGui.button("Clear Whitelist"):
                loot_filter_singleton.ClearWhitelist()
                for item in loot_items:
                    if not item.get("rarity_filter", False):
                        item["enabled"] = False
                save_loot_config()

            PyImGui.separator()
            PyImGui.text("Blacklist Actions")

            if PyImGui.button("Add ModelID to Blacklist"):
                loot_filter_singleton.AddToBlacklist(temp_model_id)
                save_loot_config()
                temp_model_id = 0

            if PyImGui.button("Remove ModelID from Blacklist"):
                loot_filter_singleton.RemoveFromBlacklist(temp_model_id)
                save_loot_config()
                temp_model_id = 0

            if PyImGui.button("Clear Blacklist"):
                loot_filter_singleton.ClearBlacklist()
                save_loot_config()

            PyImGui.end()

# --- Required Functions ---
def main():
    setup()
    render()

def configure():
    setup()

def render():
    global last_config_check_time, last_config_timestamp, last_rarity_timestamp

    current_time = time.time()
    if current_time - last_config_check_time > 2.0:
        last_config_check_time = current_time

        # Check loot_config.json
        if os.path.exists(CONFIG_FILE):
            new_timestamp = os.path.getmtime(CONFIG_FILE)
            if new_timestamp != last_config_timestamp:
                print("[INFO] Detected loot_config.json change, reloading...")
                load_loot_config()
                last_config_timestamp = new_timestamp

        # Check rarity_filter_data.json
        if os.path.exists(RARITY_FILTER_DATA_FILE):
            new_rarity_timestamp = os.path.getmtime(RARITY_FILTER_DATA_FILE)
            if new_rarity_timestamp != last_rarity_timestamp:
                print("[INFO] Detected rarity_filter_data.json change, reloading...")
                load_rarity_filter_settings()
                last_rarity_timestamp = new_rarity_timestamp

    # Draw GUI
    DrawWindow()

    if show_white_list:
        DrawWhitelistViewer()

    if show_filtered_loot_list:
        DrawFilteredLootList()

    if show_manual_editor:
        DrawManualLootConfig()

    if show_black_list:
        DrawBlacklistViewer()

# --- Exports ---
__all__ = ['main', 'configure']
