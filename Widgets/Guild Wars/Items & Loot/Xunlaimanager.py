import PyInventory
import PyImGui
import random
import time
import os
import re
import shutil
import copy

from Py4GWCoreLib import *


MODULE_NAME = "Xunlai Manager"        # Display name shown in the overlay window
MODULE_ICON = "Textures/Module_Icons/TeamInventoryViewer.png"  # Relative path to the toggle-button icon
CHEST_FRAME_ID = 752                  # Fallback frame ID for the Xunlai chest window
XUNLAI_WINDOW_HASH = 2315448754       # UIManager hash for the Xunlai vault window
FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"  # JSON file mapping human-readable frame labels
INVENTORY_FRAME_HASH = 291586130      # Fallback: player inventory panel frame hash
ANCHOR_OFFSET_X = 6                   # Horizontal gap (px) between the vault window and our overlay
ANCHOR_OFFSET_Y = 0                   # Vertical offset from the top of the vault window
COMPACT_WINDOW_MIN_WIDTH = 200        # Minimum width of the compact settings panel
COMPACT_WINDOW_MIN_HEIGHT = 230       # Minimum height of the compact settings panel
MATERIAL_STACK_MAX = 250              # Maximum quantity per material stack slot
SLOW_MODE_DELAY_MIN = 0.8             # Minimum seconds between moves in Slow Mode
SLOW_MODE_DELAY_MAX = 1.0             # Maximum seconds between moves in Slow Mode

# Runtime toggle states — persisted per-account in the INI file
ANNIVERSARY_SLOT_UNLOCKED = False  # Whether the 14th storage pane is available
SHOW_SETTINGS = False              # Whether the settings panel is expanded
SHOW_DEBUG = False                 # Whether debug log output is enabled
SLOW_MODE = False                  # Throttle moves to human-like speed (anti-bot measure)
CONSOLIDATE_TO_BACK = False        # Sort non-filter-assigned items to the back of wildcard panes so free slots appear at the front
AUTO_DEPOSIT_MATERIALS = False     # Automatically move materials into Material Storage
WINDOW_OPEN = False                # Whether the main GUI panel is visible
INI_KEY = "Xunlai Manager"
INI_RELATIVE_PATH = "Settings/{account}/Inventory/XunlaiManager/xunlai_manager.ini"


project_root = Py4GW.Console.get_projects_path()  # Absolute root path of the Py4GW installation
save_timer = ThrottledTimer(500)                   # Prevents writing the INI on every frame
_account_check_timer = ThrottledTimer(2000)        # Throttles Player.GetAccountEmail() to once every 2 s
ini_handler = None                                 # IniHandler instance; created on first account load
_active_account_email = ""                         # Email of the currently loaded account
_active_ini_path = ""                              # Full path to the active INI file
_last_saved_anniversary_slot_unlocked = False      # Tracks whether the anniversary flag needs re-saving
_selected_settings_account = ""                    # Account selected in the settings copy-from dropdown
_last_window_width = float(COMPACT_WINDOW_MIN_WIDTH)  # Cached window width used for anchor positioning

# Idle-performance: throttled stats cache — avoids scanning all storage bags every frame
_idle_refresh_timer = ThrottledTimer(2000)         # how often to recompute bag stats and sort quality
_cache_needs_refresh = True                        # set True to force immediate refresh (e.g. after sort)
_cached_available_bags = []                        # last result of _get_available_storage_bags
_cached_bag_infos = []                             # last computed per-bag info list
_cached_tabs_total_used = 0
_cached_tabs_total_size = 0
_cached_correct_items = 0
_cached_total_items = 0
_cached_correct_ratio = 1.0

# Cached UIManager anchor-position state — frame IDs are resolved once (JSON/hash lookup)
# and reused every frame; only GetFrameCoords runs each frame (fast GW memory read).
_anchor_cached_frame_id = 0           # primary vault frame ID; 0 = not yet resolved
_anchor_cached_fallback_frame_id = 0  # inventory fallback frame ID; 0 = not yet resolved
_anchor_frame_ids_resolved = False    # True once the one-time lookup has completed

# Per-bag filter state — keyed by bag_enum.value
_allowed_types_by_storage = {}              # type-name lists allowed per pane
_selected_allowed_type_idx_by_storage = {}  # selected list index in the type UI list
_selected_add_type_idx_by_storage = {}      # selected combo-box index for adding a type
_allowed_model_ids_by_storage = {}          # model-ID lists allowed per pane
_selected_allowed_model_id_idx_by_storage = {}  # selected list index in the model-ID UI list
_model_id_input_by_storage = {}             # current integer input value for adding a model ID
_selected_allowed_entry_kind_by_storage = {}    # "type" or "model" — which filter list is focused

# Sort engine constants and live state
SORT_STEPS_PER_FRAME = 8          # Max item moves executed per frame in normal mode
MAX_AUTO_SORT_RETRIES = 3         # How many placement retry rounds are allowed before giving up
MATERIAL_MAX_RESCAN_PASSES = 3    # Max deposit rescans when partial moves occurred
_sort_task_state = None           # Active sort task dict; None when idle
_sort_progress_ratio = 0.0        # 0.0–1.0 progress shown in the UI progress bar
_sort_progress_text = ""          # Human-readable status shown next to the progress bar
_sort_done_until = 0.0            # Keep progress bar visible until this monotonic timestamp
_material_storage_quantities_live = {}  # Snapshot of Material Storage quantities, refreshed each tick


def _sanitize_path_component(value: str) -> str:
	"""Strip characters that are invalid in file-system paths and return a safe folder name."""
	if not value:
		return "default_settings"
	return re.sub(r'[\\/:*?"<>|]+', "_", value).strip() or "default_settings"


def _get_current_account_email() -> str:
	"""Return the logged-in account e-mail, falling back to 'default_settings' on failure."""
	try:
		account_email = Player.GetAccountEmail()
		if account_email:
			return str(account_email)
	except Exception:
		pass
	return "default_settings"


def _build_account_ini_path(account_email: str) -> str:
	"""Build the absolute INI file path for the given account e-mail."""
	safe_account = _sanitize_path_component(account_email)
	relative_path = INI_RELATIVE_PATH.format(account=safe_account)
	return os.path.join(project_root, relative_path)


def _ensure_ini_path_exists(ini_path: str):
	"""Create the parent directory tree and an empty INI file if they do not yet exist."""
	parent_dir = os.path.dirname(ini_path)
	if parent_dir:
		os.makedirs(parent_dir, exist_ok=True)
	if not os.path.exists(ini_path):
		with open(ini_path, "w", encoding="utf-8"):
			pass


def _clear_storage_settings_cache():
	"""Discard all cached per-pane filter data so it will be re-read from the INI on next access."""
	_allowed_types_by_storage.clear()
	_selected_allowed_type_idx_by_storage.clear()
	_selected_add_type_idx_by_storage.clear()
	_allowed_model_ids_by_storage.clear()
	_selected_allowed_model_id_idx_by_storage.clear()
	_model_id_input_by_storage.clear()
	_selected_allowed_entry_kind_by_storage.clear()


def _list_settings_accounts() -> list:
	"""Return a sorted list of known account folder names that have an existing INI file."""
	accounts = set()
	settings_root = os.path.join(project_root, "Settings")
	if os.path.isdir(settings_root):
		for entry_name in os.listdir(settings_root):
			entry_path = os.path.join(settings_root, entry_name)
			if not os.path.isdir(entry_path):
				continue
			ini_path = _build_account_ini_path(entry_name)
			if os.path.exists(ini_path):
				accounts.add(entry_name)

	accounts.add(_sanitize_path_component(_get_current_account_email()))
	if _active_account_email:
		accounts.add(_sanitize_path_component(_active_account_email))

	return sorted(accounts, key=lambda value: value.lower())


def _copy_account_settings_to_current(source_account: str, target_account: str) -> bool:
	"""Copy the INI file from source_account into target_account's settings folder.

	Returns True on success, False when the source INI does not exist.
	"""
	source_account_safe = _sanitize_path_component(source_account)
	target_account_safe = _sanitize_path_component(target_account)
	source_ini_path = _build_account_ini_path(source_account_safe)
	target_ini_path = _build_account_ini_path(target_account_safe)

	if not os.path.exists(source_ini_path):
		return False

	_ensure_ini_path_exists(target_ini_path)
	shutil.copyfile(source_ini_path, target_ini_path)
	return True


def _ensure_account_settings_loaded(force: bool = False):
	"""Load (or reload) settings for the currently logged-in account.

	Creates the INI file if missing, initialises all settings globals from disk,
	and resets the active sort task and filter cache when switching accounts.
	Pass force=True to reload even if the account has not changed.
	"""
	global ini_handler
	global _active_account_email
	global _active_ini_path
	global ANNIVERSARY_SLOT_UNLOCKED
	global _last_saved_anniversary_slot_unlocked
	global SHOW_SETTINGS
	global SHOW_DEBUG
	global SLOW_MODE
	global CONSOLIDATE_TO_BACK
	global AUTO_DEPOSIT_MATERIALS
	global WINDOW_OPEN
	global _sort_task_state
	global _selected_settings_account

	# Fast-path: skip the expensive GetAccountEmail() call if already loaded and timer hasn't fired
	if not force and ini_handler is not None and not _account_check_timer.IsExpired():
		return

	runtime_account_email = _get_current_account_email()
	_account_check_timer.Reset()
	target_account_email = runtime_account_email
	ini_path = _build_account_ini_path(target_account_email)

	if not force and ini_handler is not None and ini_path == _active_ini_path:
		return

	_ensure_ini_path_exists(ini_path)
	ini_handler = IniHandler(ini_path)
	_active_account_email = target_account_email
	_selected_settings_account = _sanitize_path_component(target_account_email)
	_active_ini_path = ini_path
	ANNIVERSARY_SLOT_UNLOCKED = ini_handler.read_bool(INI_KEY, "anniversary_slot_unlocked", False)
	_last_saved_anniversary_slot_unlocked = ANNIVERSARY_SLOT_UNLOCKED
	SHOW_SETTINGS = ini_handler.read_bool(INI_KEY, "show_settings", False)
	SHOW_DEBUG = ini_handler.read_bool(INI_KEY, "show_debug", False)
	SLOW_MODE = ini_handler.read_bool(INI_KEY, "slow_mode", False)
	CONSOLIDATE_TO_BACK = ini_handler.read_bool(INI_KEY, "consolidate_to_back", False)
	AUTO_DEPOSIT_MATERIALS = ini_handler.read_bool(INI_KEY, "auto_deposit_materials", False)
	WINDOW_OPEN = ini_handler.read_bool(INI_KEY, "window_open", False)
	_sort_task_state = None
	_clear_storage_settings_cache()


_ensure_account_settings_loaded(force=True)


def _debug_log(message: str):
	"""Write message to the Py4GW console only when SHOW_DEBUG is enabled."""
	if not SHOW_DEBUG:
		return
	ConsoleLog(MODULE_NAME, message, Console.MessageType.Info)


def _set_sort_task_move_delay(task):
	"""Apply a random move delay to the task when Slow Mode is active, or clear it otherwise."""
	if not SLOW_MODE:
		task["next_move_time"] = 0.0
		task["next_move_delay"] = 0.0
		return
	delay_seconds = random.uniform(SLOW_MODE_DELAY_MIN, SLOW_MODE_DELAY_MAX)
	task["next_move_time"] = time.monotonic() + delay_seconds
	task["next_move_delay"] = delay_seconds


def _is_sort_task_waiting_for_delay(task) -> bool:
	"""Return True when the task still has a Slow Mode delay pending before the next move."""
	if not SLOW_MODE:
		return False
	return time.monotonic() < float(task.get("next_move_time", 0.0))


def _get_sort_task_delay_remaining(task) -> float:
	"""Return remaining seconds of the current Slow Mode delay, or 0.0 if none is active."""
	return max(float(task.get("next_move_time", 0.0)) - time.monotonic(), 0.0)


def _get_item_model_id(item) -> int:
	"""Return model_id from an item object, falling back to GLOBAL_CACHE lookup."""
	if hasattr(item, "model_id"):
		return int(item.model_id)
	return int(GLOBAL_CACHE.Item.GetModelID(int(item.item_id)))


def _get_item_quantity(item, default: int = 1) -> int:
	"""Return quantity from an item object, falling back to GLOBAL_CACHE lookup."""
	if hasattr(item, "quantity"):
		return int(item.quantity)
	try:
		return int(GLOBAL_CACHE.Item.Properties.GetQuantity(int(item.item_id)))
	except Exception:
		return default


# -----------------------------------------------------------------------------
# Material storage helpers
# -----------------------------------------------------------------------------
def _get_material_storage_quantities_by_model() -> dict:
	"""Return a dict mapping model_id → current quantity in Material Storage (capped at MATERIAL_STACK_MAX)."""
	quantities_by_model = {}
	try:
		material_bag = PyInventory.Bag(Bags.MaterialStorage.value, Bags.MaterialStorage.name)
		for item in material_bag.GetItems():
			if not item or int(item.item_id) == 0:
				continue
			model_id = _get_item_model_id(item)
			if model_id <= 0:
				continue
			quantity = _get_item_quantity(item)
			if quantity <= 0:
				continue
			quantities_by_model[model_id] = min(MATERIAL_STACK_MAX, quantities_by_model.get(model_id, 0) + quantity)
	except Exception:
		return quantities_by_model
	return quantities_by_model


def _is_material_storage_full_for_model(model_id: int) -> bool:
	"""Return True when the live Material Storage snapshot shows a full stack (≥250) for model_id."""
	if int(model_id) <= 0:
		return False
	quantity = int(_material_storage_quantities_live.get(int(model_id), 0))
	return quantity >= MATERIAL_STACK_MAX


def _get_material_slot_candidates_by_model_id() -> dict:
	"""Return a dict mapping known material model_ids to their preferred Material Storage slot indices.

	Used as a fallback when the item does not yet exist in Material Storage.
	"""
	fallback_slot_by_model = {}
	for model_name, slot_indices in [
		("Bone", [0]),
		("Bones", [0]),
		("Iron_Ingot", [1]),
		("Tanned_Hide_Square", [2]),
		("Scale", [3]),
		("Chitin_Fragment", [4]),
		("Bolt_Of_Cloth", [5]),
		("Wood_Plank", [6]),
		("Granite_Slab", [8]),
		("Pile_Of_Glittering_Dust", [9]),
		("Plant_Fiber", [10]),
		("Feather", [11]),
		("Fur_Square", [12]),
		("Bolt_Of_Linen", [13]),
		("Bolt_Of_Damask", [14]),
		("Bolt_Of_Silk", [15]),
		("Glob_Of_Ectoplasm", [16]),
		("Steel_Ingot", [17]),
		("Deldrimor_Steel_Ingot", [18]),
		("Monstrous_Claw", [19]),
		("Monstrous_Eye", [20]),
		("Monstrous_Fang", [21]),
		("Ruby", [22]),
		("Sapphire", [23]),
		("Diamond", [24]),
		("Onyx_Gemstone", [25]),
		("Lump_Of_Charcoal", [26]),
		("Obsidian_Shard", [27]),
		("Tempered_Glass_Vial", [29]),
		("Leather_Square", [30, 2]),
		("Elonian_Leather_Square", [31, 2]),
		("Vial_Of_Ink", [32]),
		("Roll_Of_Parchment", [33]),
		("Roll_Of_Vellum", [34]),
		("Spiritwood_Plank", [35, 6]),
		("Amber_Chunk", [36]),
		("Jadeite_Shard", [37]),
	]:
		model_member = getattr(ModelID, model_name, None)
		if model_member is None:
			continue
		try:
			fallback_slot_by_model[int(model_member.value if hasattr(model_member, "value") else model_member)] = [int(slot_index) for slot_index in slot_indices]
		except Exception:
			continue
	return fallback_slot_by_model


def _log_material_storage_counts_to_console():
	"""Dump a full slot-by-slot snapshot of Material Storage to the Py4GW console (debug helper)."""
	try:
		material_bag = PyInventory.Bag(Bags.MaterialStorage.value, Bags.MaterialStorage.name)
		material_items = material_bag.GetItems()
		bag_size = int(material_bag.GetSize())
	except Exception:
		ConsoleLog(MODULE_NAME, "Material Storage is unavailable.", Console.MessageType.Warning)
		return

	slot_entries = {}
	for item in material_items:
		if not item or int(item.item_id) == 0:
			continue
		try:
			slot_index = int(item.slot)
			model_id = _get_item_model_id(item)
			quantity = _get_item_quantity(item)
		except Exception:
			continue
		slot_entries[slot_index] = {
			"model_id": model_id,
			"quantity": max(0, quantity),
		}

	ConsoleLog(MODULE_NAME, f"Material Storage slot snapshot ({bag_size} slots)", Console.MessageType.Info)
	for slot_index in range(max(0, bag_size)):
		entry = slot_entries.get(slot_index)
		if entry is None:
			ConsoleLog(MODULE_NAME, f"Slot {slot_index}: 0", Console.MessageType.Info)
			continue

		model_id = int(entry.get("model_id", 0))
		quantity = int(entry.get("quantity", 0))
		try:
			model_name = ModelID(model_id).name if model_id > 0 else "Empty"
		except Exception:
			model_name = "Unknown"
		ConsoleLog(MODULE_NAME, f"Slot {slot_index}: ModelID {model_id} ({model_name}) = {quantity}", Console.MessageType.Info)


def _is_auto_deposit_material_candidate(item_id: int, item_type_name: str, model_id: int) -> bool:
	"""Return True when an item should be considered for Material Storage auto-deposit."""
	known_material_slots = _get_material_slot_candidates_by_model_id()
	excluded_model_ids = {
		31202,
		31203,
		31204,
	}
	if int(model_id) in excluded_model_ids:
		return False
	if int(model_id) in known_material_slots:
		return True

	if int(item_id) <= 0:
		return False

	try:
		is_zcoin = GLOBAL_CACHE.Item.Type.IsZCoin(int(item_id))
		if is_zcoin:
			return False

		is_material = GLOBAL_CACHE.Item.Type.IsMaterial(int(item_id))
		is_rare_material = GLOBAL_CACHE.Item.Type.IsRareMaterial(int(item_id))
		if is_material or is_rare_material:
			return True
		if str(item_type_name) == "Materials_Zcoins":
			return True
	except Exception:
		pass

	return False


def _collect_material_entries_for_deposit(available_storage_bags) -> list:
	"""Collect unique material candidates from inventory and storage bags (excluding Material Storage itself)."""
	entries = []
	bags_to_scan = [Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2]
	for bag_enum in available_storage_bags:
		if bag_enum != Bags.MaterialStorage:
			bags_to_scan.append(bag_enum)

	seen_item_ids = set()
	for bag_enum in bags_to_scan:
		try:
			bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
			items = bag.GetItems()
		except Exception:
			continue

		for item in items:
			if not item or int(item.item_id) == 0:
				continue
			item_id = int(item.item_id)
			if item_id in seen_item_ids:
				continue
			seen_item_ids.add(item_id)
			type_id, type_name = GLOBAL_CACHE.Item.GetItemType(item_id)
			if not type_name and int(type_id) == int(ItemType.Materials_Zcoins.value):
				type_name = "Materials_Zcoins"
			model_id = _get_item_model_id(item)
			if model_id <= 0:
				continue
			if not _is_auto_deposit_material_candidate(item_id, str(type_name or ""), model_id):
				continue
			entries.append({
				"item_id": item_id,
				"model_id": model_id,
				"bag_enum": bag_enum,
			})

	return entries


def _is_entry_excluded_from_regular_sort(entry) -> bool:
	"""Return True when an entry must be excluded from regular sorting phases.

	This protects Material Storage items and reserves non-full material candidates
	for the dedicated material-deposit phase.
	"""
	if entry.get("bag_enum") == Bags.MaterialStorage:
		return True
	if not AUTO_DEPOSIT_MATERIALS:
		return False
	model_id = int(entry.get("model_id", 0))
	if not _is_auto_deposit_material_candidate(
		int(entry.get("item_id", 0)),
		str(entry.get("type_name", "")),
		model_id,
	):
		return False
	return not _is_material_storage_full_for_model(model_id)


def _deposit_material_to_material_storage(item_id: int, model_id: int, material_storage_by_model: dict) -> int:
	"""Move up to the allowed amount of a material item into Material Storage.

	Returns moved units, 0 when nothing is moved, and -1 when no target slot can be resolved.
	"""
	fallback_slot_by_model = _get_material_slot_candidates_by_model_id()

	current_qty = int(material_storage_by_model.get(model_id, 0))
	if current_qty >= MATERIAL_STACK_MAX:
		return 0

	try:
		source_qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
	except Exception:
		source_qty = 0
	if source_qty <= 0:
		return 0

	to_move = min(source_qty, MATERIAL_STACK_MAX - current_qty)
	if to_move <= 0:
		return 0

	try:
		material_bag = PyInventory.Bag(Bags.MaterialStorage.value, Bags.MaterialStorage.name)
		material_items = material_bag.GetItems()
		bag_size = int(material_bag.GetSize())
	except Exception:
		return 0

	target_slot = None
	for material_item in material_items:
		if not material_item:
			continue
		slot = int(material_item.slot)
		candidate_model = int(material_item.model_id) if hasattr(material_item, "model_id") else 0
		if candidate_model == model_id:
			target_slot = slot
			break

	if target_slot is None:
		mapped_slots = fallback_slot_by_model.get(model_id, [])
		for mapped_slot in mapped_slots:
			if 0 <= int(mapped_slot) < max(bag_size, 0):
				target_slot = int(mapped_slot)
				break

	if target_slot is None:
		return -1

	try:
		GLOBAL_CACHE.Inventory.MoveItem(item_id, Bags.MaterialStorage.value, int(target_slot), int(to_move))
	except Exception:
		return 0

	_debug_log(
		f"Material move | item={int(item_id)} modelid={int(model_id)} qty={int(to_move)} -> {Bags.MaterialStorage.value}:{int(target_slot) + 1}"
	)

	return int(to_move)


def _start_material_phase(task, available_storage_bags, resume_phase: str):
	"""Populate task with material-deposit candidates and set phase to 'materials' (or resume_phase if none found)."""
	material_candidates = _collect_material_entries_for_deposit(available_storage_bags)
	task["material_candidates"] = material_candidates
	task["material_index"] = 0
	task["material_total"] = len(material_candidates)
	task["material_pass_index"] = 0
	task["material_moves_this_pass"] = 0
	task["material_resume_phase"] = resume_phase
	task["material_storage_by_model"] = _get_material_storage_quantities_by_model()
	task["phase"] = "materials" if len(material_candidates) > 0 else resume_phase

WEAPON_TYPE_NAMES = {
	"Axe",
	"Bow",
	"Offhand",
	"Hammer",
	"Wand",
	"Shield",
	"Staff",
	"Sword",
	"Daggers",
	"Scythe",
	"Spear",
	"Weapon",
	"MartialWeapon",
	"OffhandOrShield",
	"SpellcastingWeapon",
}

ARMOR_TYPE_NAMES = {
	"Boots",
	"Chestpiece",
	"Gloves",
	"Headpiece",
	"Leggings",
	"Leggins",
}


def _build_model_id_set_from_names(model_names):
	"""Resolve a list of ModelID attribute names to a set of integer model IDs, skipping unknowns."""
	result = set()
	for model_name in model_names:
		model_member = getattr(ModelID, model_name, None)
		if model_member is None:
			continue
		try:
			model_value = int(model_member.value if hasattr(model_member, "value") else model_member)
		except Exception:
			continue
		if model_value > 0:
			result.add(model_value)
	return result


DEFAULT_PCONS_MODEL_IDS = _build_model_id_set_from_names([
	"Armor_Of_Salvation",
	"Essence_Of_Celerity",
	"Grail_Of_Might",
	"Birthday_Cupcake",
	"Blue_Rock_Candy",
	"Green_Rock_Candy",
	"Red_Rock_Candy",
	"Bowl_Of_Skalefin_Soup",
	"Candy_Apple",
	"Candy_Corn",
	"Drake_Kabob",
	"Golden_Egg",
	"Pahnai_Salad",
	"War_Supplies",
	"Slice_Of_Pumpkin_Pie",
	"Peppermint_Candy_Cane",
	"Honeycomb",
	"Powerstone_Of_Courage",
	"Wintergreen_Candy_Cane",
	"Rainbow_Candy_Cane",
])

ALCOHOL_MODEL_IDS = _build_model_id_set_from_names([
	"Bottle_Of_Rice_Wine",
	"Eggnog",
	"Dwarven_Ale",
	"Hard_Apple_Cider",
	"Hunters_Ale",
	"Bottle_Of_Juniberry_Gin",
	"Shamrock_Ale",
	"Bottle_Of_Vabbian_Wine",
	"Vial_Of_Absinthe",
	"Witchs_Brew",
	"Zehtukas_Jug",
	"Aged_Dwarven_Ale",
	"Aged_Hunters_Ale",
	"Bottle_Of_Grog",
	"Flask_Of_Firewater",
	"Keg_Of_Aged_Hunters_Ale",
	"Krytan_Brandy",
	"Spiked_Eggnog",
	"Battle_Isle_Iced_Tea",
])

SWEETS_MODEL_IDS = _build_model_id_set_from_names([
	"Fruitcake",
	"Mandragor_Root_Cake",
	"Sugary_Blue_Drink",
	"Chocolate_Bunny",
	"Red_Bean_Cake",
	"Jar_Of_Honey",
	"Creme_Brulee",
	"Krytan_Lokum",
	"Minitreat_Of_Purity",
	"Delicious_Cake",
])

PARTY_MODEL_IDS = _build_model_id_set_from_names([
	"Bottle_Rocket",
	"Champagne_Popper",
	"Sparkler",
	"Snowman_Summoner",
	"Squash_Serum",
	"Party_Beacon",
])


SUMMONING_STONE_MODEL_IDS = _build_model_id_set_from_names([
	"Legionnaire_Summoning_Crystal",
	"Igneous_Summoning_Stone",
	"Amber_Summon",
	"Arctic_Summon",
	"Automaton_Summon",
	"Celestial_Summon",
	"Chitinous_Summon",
	"Demonic_Summon",
	"Fossilized_Summon",
	"Frosty_Summon",
	"Gelatinous_Summon",
	"Ghastly_Summon",
	"Imperial_Guard_Summon",
	"Jadeite_Summon",
	"Merchant_Summon",
	"Mischievous_Summon",
	"Mysterious_Summon",
	"Mystical_Summon",
	"Shining_Blade_Summon",
	"Tengu_Summon",
	"Zaishen_Summon",
])


def _to_roman(number: int) -> str:
	values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
	numerals = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
	result = []
	remaining = max(number, 1)
	for value, numeral in zip(values, numerals):
		while remaining >= value:
			result.append(numeral)
			remaining -= value
	return "".join(result)


def _normalize_item_type_name(type_name: str) -> str:
	"""Collapse weapon and armour sub-types and the singular 'Pcon' into canonical category names."""
	if type_name == "Pcon":
		return "Pcons"
	if type_name in WEAPON_TYPE_NAMES:
		return "Weapons"
	if type_name in ARMOR_TYPE_NAMES:
		return "Armor"
	return type_name


def _is_model_in_set(item_id: int, model_id: int | None, model_set) -> bool:
	"""Return True when the item's model_id is found in model_set.

	Resolution order: use the provided model_id if positive; otherwise query GLOBAL_CACHE.
	"""
	candidate_ids = set()
	if model_id is not None:
		try:
			parsed_model_id = int(model_id)
			if parsed_model_id > 0:
				candidate_ids.add(parsed_model_id)
		except Exception:
			pass

	if len(candidate_ids) == 0:
		try:
			cached_model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
			if cached_model_id > 0:
				candidate_ids.add(cached_model_id)
		except Exception:
			pass

	for candidate in candidate_ids:
		if candidate in model_set:
			return True
	return False


def _resolve_item_type_name(item_id: int, raw_type_name: str, model_id: int | None = None) -> str:
	"""Resolve a raw game type name to a display category used in filter rules.

	Applies model-ID-based overrides (Alcohol, Sweets, Party, Pcons, Tome, Summoning Stones)
	before falling back to the normalised type name.
	"""
	normalized = _normalize_item_type_name(raw_type_name)
	if normalized in ("Usable", "Pcons"):
		if _is_model_in_set(item_id, model_id, ALCOHOL_MODEL_IDS):
			return "Alcohol"
		if _is_model_in_set(item_id, model_id, SWEETS_MODEL_IDS):
			return "Sweets"
		if _is_model_in_set(item_id, model_id, PARTY_MODEL_IDS):
			return "Party"
	if _is_model_in_set(item_id, model_id, DEFAULT_PCONS_MODEL_IDS):
		return "Pcons"
	if normalized == "Usable":
		if GLOBAL_CACHE.Item.Type.IsTome(item_id):
			return "Tome"
		if _is_model_in_set(item_id, model_id, SUMMONING_STONE_MODEL_IDS):
			return "Summoning Stones"
	return normalized


# -----------------------------------------------------------------------------
# Item classification and sort rule helpers
# -----------------------------------------------------------------------------
def _build_item_type_options() -> list:
	"""Build the sorted list of all selectable item-type filter labels for the settings UI."""
	options = []
	for item_type in ItemType:
		normalized = _normalize_item_type_name(item_type.name)
		if normalized not in options:
			options.append(normalized)
	if "Tome" not in options:
		options.append("Tome")
	if "Pcons" not in options:
		options.append("Pcons")
	if "Summoning Stones" not in options:
		options.append("Summoning Stones")
	if "Alcohol" not in options:
		options.append("Alcohol")
	if "Sweets" not in options:
		options.append("Sweets")
	if "Party" not in options:
		options.append("Party")
	return options


ITEM_TYPE_OPTIONS = _build_item_type_options()



def _load_allowed_types_for_storage(bag_enum):
	"""Return the cached (or freshly loaded) list of allowed item-type names for a storage pane."""
	bag_key = bag_enum.value
	if bag_key in _allowed_types_by_storage:
		return _allowed_types_by_storage[bag_key]

	raw = ini_handler.read_key(INI_KEY, f"allowed_item_types_storage_{bag_enum.value}", "")
	parsed = []
	for token in raw.split(","):
		name = token.strip()
		if not name:
			continue
		name = _normalize_item_type_name(name)
		if name in ITEM_TYPE_OPTIONS and name not in parsed:
			parsed.append(name)

	_allowed_types_by_storage[bag_key] = parsed
	_selected_allowed_type_idx_by_storage[bag_key] = 0
	_selected_add_type_idx_by_storage[bag_key] = 0
	if bag_key not in _selected_allowed_entry_kind_by_storage:
		_selected_allowed_entry_kind_by_storage[bag_key] = "type"
	return _allowed_types_by_storage[bag_key]


def _load_allowed_model_ids_for_storage(bag_enum):
	"""Return the cached (or freshly loaded) list of allowed model IDs for a storage pane."""
	bag_key = bag_enum.value
	if bag_key in _allowed_model_ids_by_storage:
		return _allowed_model_ids_by_storage[bag_key]

	raw = ini_handler.read_key(INI_KEY, f"allowed_model_ids_storage_{bag_enum.value}", "")
	parsed = []
	for token in raw.split(","):
		text = token.strip()
		if not text:
			continue
		try:
			model_id = int(text)
		except Exception:
			continue
		if model_id <= 0:
			continue
		if model_id not in parsed:
			parsed.append(model_id)

	_allowed_model_ids_by_storage[bag_key] = parsed
	_selected_allowed_model_id_idx_by_storage[bag_key] = 0
	_model_id_input_by_storage[bag_key] = 0
	if bag_key not in _selected_allowed_entry_kind_by_storage:
		_selected_allowed_entry_kind_by_storage[bag_key] = "type"
	return _allowed_model_ids_by_storage[bag_key]


def _save_allowed_types_for_storage(bag_enum):
	"""Persist the allowed item-type list for a storage pane to the INI file."""
	bag_key = bag_enum.value
	allowed = _allowed_types_by_storage.get(bag_key, [])
	ini_handler.write_key(INI_KEY, f"allowed_item_types_storage_{bag_enum.value}", ",".join(allowed))


def _save_allowed_model_ids_for_storage(bag_enum):
	"""Persist the allowed model-ID list for a storage pane to the INI file."""
	bag_key = bag_enum.value
	allowed = _allowed_model_ids_by_storage.get(bag_key, [])
	ini_handler.write_key(INI_KEY, f"allowed_model_ids_storage_{bag_enum.value}", ",".join(str(model_id) for model_id in allowed))


def _has_any_model_id_filters(available_storage_bags) -> bool:
	"""Return True when at least one storage pane has a model-ID filter configured."""
	for bag_enum in available_storage_bags:
		if len(_load_allowed_model_ids_for_storage(bag_enum)) > 0:
			return True
	return False


def _is_item_model_id_allowed(model_id: int, allowed_model_ids) -> bool:
	"""Return True when the model-ID list is empty (no filter) or the ID is explicitly listed."""
	if len(allowed_model_ids) == 0:
		return True
	return int(model_id) in allowed_model_ids


def _matches_storage_rules(item_type_name: str, model_id: int, allowed_types, allowed_model_ids) -> bool:
	"""Return True when the item satisfies the type and/or model-ID filters of a pane.

	When both filters are set, either matching is sufficient (OR logic).
	When neither is set, everything is allowed.
	"""
	type_filtered = len(allowed_types) > 0
	model_filtered = len(allowed_model_ids) > 0

	if not type_filtered and not model_filtered:
		return True
	if type_filtered and not model_filtered:
		return item_type_name in allowed_types
	if not type_filtered and model_filtered:
		return int(model_id) in allowed_model_ids

	return (item_type_name in allowed_types) or (int(model_id) in allowed_model_ids)


def _storage_allows_all_types(allowed_types) -> bool:
	"""Return True when the type filter is empty or covers every possible item type."""
	if len(allowed_types) == 0:
		return True
	return len(set(allowed_types)) >= len(set(ITEM_TYPE_OPTIONS))


def _storage_allows_all_model_ids(allowed_model_ids) -> bool:
	"""Return True when no model-ID filter is configured (empty list means accept all)."""
	return len(allowed_model_ids) == 0


def _storage_is_all_allowed(allowed_types, allowed_model_ids) -> bool:
	"""Return True when a pane has no restrictions at all (wildcard pane)."""
	return _storage_allows_all_types(allowed_types) and _storage_allows_all_model_ids(allowed_model_ids)


def _build_allowed_type_map(available_storage_bags):
	"""Build lookup structures for the sort engine based on the per-pane filter settings.

	Returns:
		allowed_by_bag         — type lists keyed by bag_enum
		allowed_models_by_bag  — model-ID lists keyed by bag_enum
		filtered_bags_by_type  — bags that explicitly accept a given type name
		filtered_bags_by_model_id — bags that explicitly accept a given model ID
		wildcard_bags          — bags with no type or model restrictions
		wildcard_model_bags    — bags with no model-ID restrictions
	"""
	allowed_by_bag = {}
	allowed_models_by_bag = {}
	filtered_bags_by_type = {}
	filtered_bags_by_model_id = {}
	wildcard_bags = []
	wildcard_model_bags = []

	for bag_enum in available_storage_bags:
		allowed_types = _load_allowed_types_for_storage(bag_enum)
		allowed_model_ids = _load_allowed_model_ids_for_storage(bag_enum)
		allowed_by_bag[bag_enum] = allowed_types
		allowed_models_by_bag[bag_enum] = allowed_model_ids
		if _storage_is_all_allowed(allowed_types, allowed_model_ids):
			wildcard_bags.append(bag_enum)
		else:
			for type_name in allowed_types:
				if type_name not in filtered_bags_by_type:
					filtered_bags_by_type[type_name] = []
				filtered_bags_by_type[type_name].append(bag_enum)

		if _storage_allows_all_model_ids(allowed_model_ids):
			wildcard_model_bags.append(bag_enum)
		else:
			for model_id in allowed_model_ids:
				if model_id not in filtered_bags_by_model_id:
					filtered_bags_by_model_id[model_id] = []
				filtered_bags_by_model_id[model_id].append(bag_enum)

	return (
		allowed_by_bag,
		allowed_models_by_bag,
		filtered_bags_by_type,
		filtered_bags_by_model_id,
		wildcard_bags,
		wildcard_model_bags,
	)


def _is_item_in_correct_storage(
	source_bag_enum,
	item_type_name: str,
	model_id: int,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
) -> bool:
	"""Return True when the item is already sitting in the correct storage pane.

	Model-ID filters take priority over type filters. An item in a wildcard pane is
	considered wrong if a dedicated (filtered) pane exists for its type or model.
	"""
	allowed_types = allowed_by_bag.get(source_bag_enum, [])
	allowed_model_ids = allowed_models_by_bag.get(source_bag_enum, [])
	model_id = int(model_id)
	target_filtered_model_bags = filtered_bags_by_model_id.get(model_id, [])
	has_model_priority = len(target_filtered_model_bags) > 0

	if has_model_priority:
		if not _is_item_model_id_allowed(model_id, allowed_model_ids):
			return False
		return source_bag_enum in target_filtered_model_bags

	if not _matches_storage_rules(item_type_name, model_id, allowed_types, allowed_model_ids):
		return False

	if _storage_is_all_allowed(allowed_types, allowed_model_ids):
		target_filtered_bags = filtered_bags_by_type.get(item_type_name, [])
		if len(target_filtered_bags) > 0:
			return False

	return True


# -----------------------------------------------------------------------------
# Sort engine (collect, move, phase processing)
# -----------------------------------------------------------------------------
def _collect_storage_item_entries(available_storage_bags):
	"""Scan all available storage panes and return a snapshot of every item.

	Returns:
		entries    — list of item dicts (item_id, type_name, model_id, quantity, bag_enum, slot, …)
		bag_states — dict mapping bag_enum to {size, occupied_slots, free_slots}
	"""
	bag_states = {}
	entries = []

	for bag_enum in available_storage_bags:
		try:
			bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
			size = int(bag.GetSize())
			items = bag.GetItems()
		except Exception:
			size = 0
			items = []

		occupied_slots = set()
		for item in items:
			if not item or item.item_id == 0:
				continue

			model_id = _get_item_model_id(item)
			type_id, type_name = GLOBAL_CACHE.Item.GetItemType(item.item_id)
			if not type_name:
				type_name = f"Type {type_id}"
			type_name = _resolve_item_type_name(item.item_id, type_name, model_id)

			slot = int(item.slot)
			occupied_slots.add(slot)
			quantity = _get_item_quantity(item)
			if quantity <= 0:
				quantity = 1
			is_stackable = GLOBAL_CACHE.Item.Customization.IsStackable(item.item_id)
			dye_key = None
			if model_id == ModelID.Vial_Of_Dye.value:
				try:
					dye_info = GLOBAL_CACHE.Item.Customization.GetDyeInfo(item.item_id)
					dye_key = int(dye_info.dye1.ToInt())
				except Exception:
					dye_key = None

			entries.append(
				{
					"item_id": int(item.item_id),
					"type_name": type_name,
					"model_id": model_id,
					"is_stackable": bool(is_stackable),
					"dye_key": dye_key,
					"quantity": quantity,
					"bag_enum": bag_enum,
					"slot": slot,
				}
			)

		free_slots = sorted([slot for slot in range(max(size, 0)) if slot not in occupied_slots])
		bag_states[bag_enum] = {
			"size": size,
			"occupied_slots": occupied_slots,
			"free_slots": free_slots,
		}

	return entries, bag_states


def _consolidate_storage_stacks(
	entries,
	bag_states,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
):
	"""Merge partial stacks of the same item together before placement sorting begins.

	Full stacks (quantity == MATERIAL_STACK_MAX) that are already in the correct pane
	are protected from being used as donors. Material Storage entries and auto-deposit
	candidates are skipped entirely.
	"""
	max_stack_size = MATERIAL_STACK_MAX
	moved_actions = 0
	protected_item_ids = set()

	for entry in entries:
		if _is_entry_excluded_from_regular_sort(entry):
			continue

		if entry.get("quantity", 0) < max_stack_size:
			continue
		if _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		):
			protected_item_ids.add(entry["item_id"])

	grouped_entries = {}
	for entry in entries:
		if _is_entry_excluded_from_regular_sort(entry):
			continue

		if entry.get("quantity", 0) <= 0:
			continue
		merge_key = (entry.get("model_id", 0), entry.get("dye_key", None)) if entry.get("is_stackable", False) else None
		if merge_key is None:
			continue
		if merge_key not in grouped_entries:
			grouped_entries[merge_key] = []
		grouped_entries[merge_key].append(entry)

	for _, same_item_entries in grouped_entries.items():
		targets = [entry for entry in same_item_entries if 0 < entry.get("quantity", 0) < max_stack_size]
		donors = [
			entry
			for entry in same_item_entries
			if entry.get("quantity", 0) > 0 and entry.get("item_id") not in protected_item_ids
		]

		targets.sort(key=lambda entry: entry["quantity"])
		donors.sort(key=lambda entry: entry["quantity"], reverse=True)

		for target in targets:
			while target["quantity"] < max_stack_size:
				needed = max_stack_size - target["quantity"]
				if needed <= 0:
					break

				donor_found = None
				for donor in donors:
					if donor["item_id"] == target["item_id"]:
						continue
					if donor.get("quantity", 0) <= 0:
						continue
					donor_found = donor
					break

				if donor_found is None:
					break

				move_amount = min(needed, donor_found["quantity"])
				if move_amount <= 0:
					break

				GLOBAL_CACHE.Inventory.MoveItem(
					donor_found["item_id"],
					target["bag_enum"].value,
					target["slot"],
					move_amount,
				)

				_debug_log(
					f"Stack merge | donor_item={int(donor_found['item_id'])} ({donor_found['bag_enum'].value}:{int(donor_found['slot']) + 1}) -> target_item={int(target['item_id'])} ({target['bag_enum'].value}:{int(target['slot']) + 1}) qty={int(move_amount)}"
				)

				donor_found["quantity"] -= move_amount
				target["quantity"] += move_amount
				moved_actions += 1

				if donor_found["quantity"] <= 0:
					donor_found["quantity"] = 0
					source_state = bag_states.get(donor_found["bag_enum"])
					if source_state is not None:
						source_slot = donor_found["slot"]
						source_state["occupied_slots"].discard(source_slot)
						if source_slot not in source_state["free_slots"] and 0 <= source_slot < source_state["size"]:
							source_state["free_slots"].append(source_slot)
							source_state["free_slots"].sort()

	entries[:] = [entry for entry in entries if entry.get("quantity", 0) > 0]
	return moved_actions


def _get_next_free_slot(bag_states, bag_enum):
	"""Return the lowest free slot index in bag_enum, or None if no free slot exists."""
	state = bag_states.get(bag_enum)
	if not state:
		return None
	if len(state["free_slots"]) == 0:
		return None
	return state["free_slots"][0]


def _reserve_move_in_state(bag_states, source_bag_enum, source_slot: int, target_bag_enum, target_slot: int):
	"""Update bag_states slot bookkeeping to reflect a pending move (no actual game API call)."""
	source = bag_states.get(source_bag_enum)
	target = bag_states.get(target_bag_enum)
	if source:
		source["occupied_slots"].discard(source_slot)
		if source_slot not in source["free_slots"] and 0 <= source_slot < source["size"]:
			source["free_slots"].append(source_slot)
			source["free_slots"].sort()
	if target:
		if target_slot in target["free_slots"]:
			target["free_slots"].remove(target_slot)
		target["occupied_slots"].add(target_slot)


def _find_any_free_slot(bag_states, bag_order, blocked_slots=None):
	"""Return the first (bag_enum, slot) pair that is free and not in blocked_slots.

	Panes are searched in bag_order priority. Returns (None, None) when nothing is available.
	"""
	if blocked_slots is None:
		blocked_slots = set()

	for bag_enum in bag_order:
		state = bag_states.get(bag_enum)
		if state is None:
			continue
		for slot in state.get("free_slots", []):
			if (bag_enum, slot) in blocked_slots:
				continue
			return bag_enum, slot

	return None, None


def _move_entry_to_slot(entry, target_bag_enum, target_slot: int, bag_states, dry_run: bool = False) -> bool:
	"""Move an item entry to the given slot, update bag_states, and mutate entry in-place.

	When dry_run=True the game API is not called; only the in-memory state is updated.
	Returns True on success (or when the item is already at the target), False on API error.
	"""
	source_bag = entry["bag_enum"]
	source_slot = entry["slot"]
	if source_bag == target_bag_enum and source_slot == target_slot:
		return True

	if not dry_run:
		try:
			GLOBAL_CACHE.Inventory.MoveItem(entry["item_id"], target_bag_enum.value, target_slot, entry["quantity"])
		except Exception:
			return False

		_debug_log(
			f"Move | item={int(entry.get('item_id', 0))} modelid={int(entry.get('model_id', 0))} type={str(entry.get('type_name', 'Unknown'))} qty={int(entry.get('quantity', 0))} {source_bag.value}:{int(source_slot) + 1} -> {target_bag_enum.value}:{int(target_slot) + 1}"
		)

	_reserve_move_in_state(bag_states, source_bag, source_slot, target_bag_enum, target_slot)
	entry["bag_enum"] = target_bag_enum
	entry["slot"] = target_slot
	return True


def _get_model_sort_type_priority(type_name: str):
	"""Return a (index, name) sort key for a type name based on ITEM_TYPE_OPTIONS order.

	Unknown types sort after all known types.
	"""
	try:
		return ITEM_TYPE_OPTIONS.index(type_name), type_name
	except ValueError:
		return len(ITEM_TYPE_OPTIONS), type_name


def _sort_items_within_storage_by_model_id(entries, bag_states, available_storage_bags, target_bags=None, max_move_actions=None, dry_run: bool = False):
	"""Sort items within each pane by (type priority, model_id, item_id) using in-place swaps.

	When max_move_actions is set (Slow Mode), stops after that many moves and signals incompletion
	via completed_all_bags=False. Returns (total_moves, unresolved_bags, completed_all_bags).
	"""
	move_actions = 0
	unresolved_bags = 0
	completed_all_bags = True
	bags_to_process = target_bags if target_bags is not None else available_storage_bags

	for bag_enum in bags_to_process:
		if bag_enum == Bags.MaterialStorage:
			continue

		bag_entries = [
			entry
			for entry in entries
			if entry.get("bag_enum") == bag_enum
			and entry.get("quantity", 0) > 0
			and not _is_entry_excluded_from_regular_sort(entry)
		]
		if len(bag_entries) <= 1:
			continue

		target_slots = sorted(entry["slot"] for entry in bag_entries)
		desired_entries = sorted(
			bag_entries,
			key=lambda entry: (
				_get_model_sort_type_priority(str(entry.get("type_name", "")))
				+ (int(entry.get("model_id", 0)), int(entry.get("item_id", 0)))
			),
		)
		desired_slot_by_item_id = {
			desired_entries[index]["item_id"]: target_slots[index] for index in range(len(desired_entries))
		}

		slot_to_entry = {entry["slot"]: entry for entry in bag_entries if entry.get("bag_enum") == bag_enum}

		for desired_entry in desired_entries:
			target_slot = desired_slot_by_item_id[desired_entry["item_id"]]
			if desired_entry.get("bag_enum") == bag_enum and desired_entry.get("slot") == target_slot:
				continue

			occupant = slot_to_entry.get(target_slot)
			moved_occupant = False
			occupant_original_slot = target_slot

			if occupant is not None and occupant.get("item_id") != desired_entry.get("item_id"):
				free_slot = _get_next_free_slot(bag_states, bag_enum)
				if free_slot is None:
					continue

				if not _move_entry_to_slot(occupant, bag_enum, free_slot, bag_states, dry_run=dry_run):
					continue

				moved_occupant = True
				slot_to_entry.pop(occupant_original_slot, None)
				slot_to_entry[free_slot] = occupant
				move_actions += 1

			source_bag_before = desired_entry["bag_enum"]
			source_slot_before = desired_entry["slot"]
			if not _move_entry_to_slot(desired_entry, bag_enum, target_slot, bag_states, dry_run=dry_run):
				if moved_occupant:
					if _move_entry_to_slot(occupant, bag_enum, occupant_original_slot, bag_states, dry_run=dry_run):
						slot_to_entry[occupant_original_slot] = occupant
				continue

			if source_bag_before == bag_enum:
				slot_to_entry.pop(source_slot_before, None)
			slot_to_entry[target_slot] = desired_entry
			move_actions += 1
			if max_move_actions is not None and move_actions >= max_move_actions:
				completed_all_bags = False
				return move_actions, unresolved_bags, completed_all_bags

		if any(
			entry.get("bag_enum") != bag_enum or entry.get("slot") != desired_slot_by_item_id.get(entry.get("item_id"), -1)
			for entry in desired_entries
		):
			unresolved_bags += 1

	return move_actions, unresolved_bags, completed_all_bags


def _compact_storage_slots(entries, bag_states, available_storage_bags, target_bags=None, max_move_actions=None, dry_run: bool = False):
	"""Shift items toward the front of each pane to fill gaps left by completed moves.

	When max_move_actions is set (Slow Mode), stops early and signals incompletion
	via completed_all_bags=False. Returns (move_actions, completed_all_bags).
	"""
	move_actions = 0
	completed_all_bags = True
	bags_to_process = target_bags if target_bags is not None else available_storage_bags

	for bag_enum in bags_to_process:
		if bag_enum == Bags.MaterialStorage:
			continue

		bag_entries = [
			entry
			for entry in entries
			if entry.get("bag_enum") == bag_enum
			and entry.get("quantity", 0) > 0
			and not _is_entry_excluded_from_regular_sort(entry)
		]
		if len(bag_entries) <= 1:
			continue

		bag_entries.sort(key=lambda entry: int(entry.get("slot", 0)))
		for compact_slot, entry in enumerate(bag_entries):
			current_slot = int(entry.get("slot", 0))
			if current_slot == compact_slot:
				continue

			if not _move_entry_to_slot(entry, bag_enum, compact_slot, bag_states, dry_run=dry_run):
				continue

			move_actions += 1
			if max_move_actions is not None and move_actions >= max_move_actions:
				completed_all_bags = False
				return move_actions, completed_all_bags

	return move_actions, completed_all_bags


def _count_consolidate_back_items(
	entries,
	bag_states,
	available_storage_bags,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
) -> int:
	"""Return the number of consolidatable items not already at their target back-positions.

	Uses the same slot-assignment logic as _consolidate_items_to_back but only counts
	rather than moving anything.
	"""
	eligible_bags_set = set()
	nc_slots_by_bag = {}
	eligible_bags_ordered = []

	for bag_enum in available_storage_bags:
		if bag_enum == Bags.MaterialStorage:
			continue
		if not _storage_is_all_allowed(allowed_by_bag.get(bag_enum, []), allowed_models_by_bag.get(bag_enum, [])):
			continue
		state = bag_states.get(bag_enum)
		if state is None or int(state.get("size", 0)) == 0:
			continue
		nc_slots = set()
		for entry in entries:
			if entry.get("bag_enum") != bag_enum or entry.get("quantity", 0) <= 0:
				continue
			if _is_entry_excluded_from_regular_sort(entry):
				nc_slots.add(entry["slot"])
				continue
			type_name = entry.get("type_name", "")
			model_id = int(entry.get("model_id", 0))
			if type_name in filtered_bags_by_type or model_id in filtered_bags_by_model_id:
				nc_slots.add(entry["slot"])
		nc_slots_by_bag[bag_enum] = nc_slots
		eligible_bags_ordered.append(bag_enum)
		eligible_bags_set.add(bag_enum)

	if not eligible_bags_ordered:
		return 0

	combined_movable = []
	for bag_enum in eligible_bags_ordered:
		state = bag_states.get(bag_enum)
		bag_size = int(state.get("size", 0))
		nc_slots = nc_slots_by_bag[bag_enum]
		for slot in range(bag_size):
			if slot not in nc_slots:
				combined_movable.append((bag_enum, slot))

	consolidatable = []
	for entry in entries:
		be = entry.get("bag_enum")
		if be not in eligible_bags_set or entry.get("quantity", 0) <= 0:
			continue
		if _is_entry_excluded_from_regular_sort(entry):
			continue
		type_name = entry.get("type_name", "")
		model_id = int(entry.get("model_id", 0))
		if type_name in filtered_bags_by_type or model_id in filtered_bags_by_model_id:
			continue
		consolidatable.append(entry)

	n_items = len(consolidatable)
	if n_items == 0 or len(combined_movable) < n_items:
		return 0

	consolidatable_sorted = sorted(
		consolidatable,
		key=lambda e: (
			_get_model_sort_type_priority(str(e.get("type_name", "")))
			+ (int(e.get("model_id", 0)), int(e.get("item_id", 0)))
		),
	)
	target_positions = combined_movable[len(combined_movable) - n_items:]
	count = 0
	for i, entry in enumerate(consolidatable_sorted):
		t_bag, t_slot = target_positions[i]
		if entry.get("bag_enum") != t_bag or entry.get("slot") != t_slot:
			count += 1
	return count


def _consolidate_items_to_back(
	entries,
	bag_states,
	available_storage_bags,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
	max_move_actions=None,
	dry_run: bool = False,
):
	"""Push items in wildcard panes toward the end so that free slots accumulate at the front.

	All eligible wildcard panes (no type filter AND no model-ID filter) are treated as a
	single combined slot space. Items are sorted by (type_priority, model_id, item_id) and
	assigned to the last N combined movable slots so they pack contiguously to the rear
	across tab boundaries. Non-consolidatable items (excluded from regular sort, or belonging
	to a dedicated filtered pane) are never displaced and their slots are not used as targets.

	Returns (move_actions, completed). completed=False means stopped early due to max_move_actions.
	"""
	move_actions = 0

	# ── Step 1: identify eligible wildcard bags and per-bag non-consolidatable slot sets ──
	eligible_bags_ordered = []
	nc_slots_by_bag = {}  # bag_enum -> set of slots occupied by non-consolidatable items

	for bag_enum in available_storage_bags:
		if bag_enum == Bags.MaterialStorage:
			continue
		allowed_types = allowed_by_bag.get(bag_enum, [])
		allowed_model_ids = allowed_models_by_bag.get(bag_enum, [])
		if not _storage_is_all_allowed(allowed_types, allowed_model_ids):
			continue
		state = bag_states.get(bag_enum)
		if state is None or int(state.get("size", 0)) == 0:
			continue

		nc_slots = set()
		for entry in entries:
			if entry.get("bag_enum") != bag_enum or entry.get("quantity", 0) <= 0:
				continue
			if _is_entry_excluded_from_regular_sort(entry):
				nc_slots.add(entry["slot"])
				continue
			type_name = entry.get("type_name", "")
			model_id = int(entry.get("model_id", 0))
			if type_name in filtered_bags_by_type or model_id in filtered_bags_by_model_id:
				nc_slots.add(entry["slot"])

		nc_slots_by_bag[bag_enum] = nc_slots
		eligible_bags_ordered.append(bag_enum)

	if not eligible_bags_ordered:
		return 0, True

	eligible_bags_set = set(eligible_bags_ordered)

	# ── Step 2: build combined ordered list of movable (bag, slot) positions ──
	# Iterate panes in order; within each pane iterate slots in order.
	# Slots occupied by non-consolidatable items are excluded.
	combined_movable = []  # [(bag_enum, slot), ...]
	for bag_enum in eligible_bags_ordered:
		state = bag_states.get(bag_enum)
		bag_size = int(state.get("size", 0))
		nc_slots = nc_slots_by_bag[bag_enum]
		for slot in range(bag_size):
			if slot not in nc_slots:
				combined_movable.append((bag_enum, slot))

	# ── Step 3: collect all consolidatable items from all eligible bags ──
	all_consolidatable = []
	for entry in entries:
		be = entry.get("bag_enum")
		if be not in eligible_bags_set or entry.get("quantity", 0) <= 0:
			continue
		if _is_entry_excluded_from_regular_sort(entry):
			continue
		type_name = entry.get("type_name", "")
		model_id = int(entry.get("model_id", 0))
		if type_name in filtered_bags_by_type or model_id in filtered_bags_by_model_id:
			continue
		all_consolidatable.append(entry)

	n_items = len(all_consolidatable)
	if n_items <= 1 or len(combined_movable) < n_items:
		return 0, True

	# ── Step 4: sort items and assign the LAST N combined movable positions as targets ──
	all_consolidatable_sorted = sorted(
		all_consolidatable,
		key=lambda e: (
			_get_model_sort_type_priority(str(e.get("type_name", "")))
			+ (int(e.get("model_id", 0)), int(e.get("item_id", 0)))
		),
	)
	target_positions = combined_movable[len(combined_movable) - n_items:]  # last N, in pane order
	desired_target_by_item_id = {
		all_consolidatable_sorted[i]["item_id"]: target_positions[i]
		for i in range(n_items)
	}

	# ── Step 5: build (bag_enum, slot) -> entry for all items in eligible bags ──
	slot_to_entry = {}  # (bag_enum, slot) -> entry
	for entry in entries:
		be = entry.get("bag_enum")
		if be in eligible_bags_set and entry.get("quantity", 0) > 0:
			slot_to_entry[(be, entry["slot"])] = entry

	# ── Step 6: execute moves in sorted order ──
	# move_actions counts only successful PLACEMENTS (not evictions).
	# max_move_actions limits placements per call so the progress bar advances smoothly.
	for desired_entry in all_consolidatable_sorted:
		target_bag, target_slot = desired_target_by_item_id[desired_entry["item_id"]]
		current_bag = desired_entry.get("bag_enum")
		current_slot = desired_entry.get("slot")

		if current_bag == target_bag and current_slot == target_slot:
			continue

		occupant = slot_to_entry.get((target_bag, target_slot))
		if occupant is not None and occupant.get("item_id") != desired_entry.get("item_id"):
			# Find any free movable slot across all eligible bags to evict the occupant
			free_bag, free_slot = None, None
			for fb in eligible_bags_ordered:
				fb_state = bag_states.get(fb)
				if fb_state is None:
					continue
				nc = nc_slots_by_bag.get(fb, set())
				for fs in fb_state.get("free_slots", []):
					if fs not in nc:
						free_bag, free_slot = fb, fs
						break
				if free_bag is not None:
					break
			if free_bag is None:
				continue
			if not _move_entry_to_slot(occupant, free_bag, free_slot, bag_states, dry_run=dry_run):
				continue
			slot_to_entry.pop((target_bag, target_slot), None)
			slot_to_entry[(free_bag, free_slot)] = occupant
			# Eviction is not counted in move_actions — only placements are

		src_bag = desired_entry.get("bag_enum")
		src_slot = desired_entry.get("slot")
		if not _move_entry_to_slot(desired_entry, target_bag, target_slot, bag_states, dry_run=dry_run):
			continue
		slot_to_entry.pop((src_bag, src_slot), None)
		slot_to_entry[(target_bag, target_slot)] = desired_entry
		move_actions += 1  # count only successful placements
		if max_move_actions is not None and move_actions >= max_move_actions:
			return move_actions, False

	return move_actions, True


def _plan_sort_moves(
	entries_orig,
	bag_states_orig,
	available_storage_bags,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
	wildcard_bags,
	wildcard_model_bags,
	consolidate_to_back,
):
	"""Simulate all sort phases (no API calls) and compute the final position of every item.

	Returns {item_id: (target_bag, target_slot)} for items whose final position differs
	from their current position. Used to build the execute-phase move plan.
	"""
	entries = copy.deepcopy(entries_orig)
	bag_states = copy.deepcopy(bag_states_orig)
	initial_pos = {
		e["item_id"]: (e["bag_enum"], e["slot"])
		for e in entries
		if e.get("quantity", 0) > 0
	}

	# Simulate placement rounds to completion (no frame throttle needed)
	for _ in range(MAX_AUTO_SORT_RETRIES + 1):
		wrong = _build_wrong_entries(
			entries, allowed_by_bag, allowed_models_by_bag,
			filtered_bags_by_type, filtered_bags_by_model_id, available_storage_bags,
		)
		if not wrong:
			break
		moved_any = False
		for entry in wrong:
			if _try_move_wrong_entry(
				entry, available_storage_bags, allowed_by_bag, allowed_models_by_bag,
				filtered_bags_by_type, filtered_bags_by_model_id,
				wildcard_bags, wildcard_model_bags, bag_states, dry_run=True,
			):
				moved_any = True
		if not moved_any:
			break

	# Simulate model sort
	_sort_items_within_storage_by_model_id(entries, bag_states, available_storage_bags, dry_run=True)

	# Simulate compaction
	_compact_storage_slots(entries, bag_states, available_storage_bags, dry_run=True)

	# Simulate consolidate-to-back (if enabled)
	if consolidate_to_back:
		_consolidate_items_to_back(
			entries, bag_states, available_storage_bags,
			allowed_by_bag, allowed_models_by_bag,
			filtered_bags_by_type, filtered_bags_by_model_id,
			dry_run=True,
		)

	# Build plan from simulated vs. initial positions
	plan = {}
	for entry in entries:
		item_id = entry.get("item_id")
		if item_id is None or entry.get("quantity", 0) <= 0:
			continue
		initial = initial_pos.get(item_id)
		if initial is None:
			continue
		final = (entry["bag_enum"], entry["slot"])
		if final != initial:
			plan[item_id] = final

	return plan


def _execute_move_plan(entries, bag_states, move_plan, available_storage_bags, max_moves=None):
	"""Execute moves from the pre-computed plan. Returns (plan_moves_done, completed).

	Items are moved to their planned final positions. If a target slot is occupied by an
	item that has no planned move, that occupant is evicted to a free slot first. Cycles
	(two or more pending items mutually blocking each other) are broken by moving one item
	to a free buffer slot.

	max_moves limits total API calls per frame (evictions and placements combined).
	plan_moves_done counts only items that reached their planned final target.
	"""
	if not move_plan:
		return 0, True

	entry_by_id = {e["item_id"]: e for e in entries}
	slot_to_id = {}
	for e in entries:
		if e.get("quantity", 0) > 0:
			slot_to_id[(e["bag_enum"], e["slot"])] = e["item_id"]

	pending = set()
	for iid, (tb, ts) in move_plan.items():
		en = entry_by_id.get(iid)
		if en is not None and (en["bag_enum"] != tb or en["slot"] != ts):
			pending.add(iid)

	plan_moves_done = 0
	total_api_calls = 0

	while pending:
		if max_moves is not None and total_api_calls >= max_moves:
			break
		made_progress = False

		for item_id in list(pending):
			if max_moves is not None and total_api_calls >= max_moves:
				break
			entry = entry_by_id.get(item_id)
			if entry is None or entry.get("quantity", 0) <= 0:
				pending.discard(item_id)
				made_progress = True
				continue
			target_bag, target_slot = move_plan[item_id]
			if entry["bag_enum"] == target_bag and entry["slot"] == target_slot:
				pending.discard(item_id)
				made_progress = True
				continue
			occupant_id = slot_to_id.get((target_bag, target_slot))

			if occupant_id is None:
				# Target slot is free — move directly
				src_bag, src_slot = entry["bag_enum"], entry["slot"]
				if _move_entry_to_slot(entry, target_bag, target_slot, bag_states):
					slot_to_id.pop((src_bag, src_slot), None)
					slot_to_id[(target_bag, target_slot)] = item_id
					total_api_calls += 1
					plan_moves_done += 1
				pending.discard(item_id)
				made_progress = True

			elif occupant_id in pending:
				# Occupant also needs to move — wait for it to free the slot
				pass

			else:
				# Occupant has no planned move — evict it, then place our item
				free_bag, free_slot = _find_any_free_slot(bag_states, available_storage_bags)
				if free_bag is None:
					continue
				occ = entry_by_id.get(occupant_id)
				if occ is None:
					continue
				occ_bag, occ_slot = occ["bag_enum"], occ["slot"]
				if _move_entry_to_slot(occ, free_bag, free_slot, bag_states):
					slot_to_id.pop((occ_bag, occ_slot), None)
					slot_to_id[(free_bag, free_slot)] = occupant_id
					total_api_calls += 1
				if max_moves is not None and total_api_calls >= max_moves:
					break
				src_bag, src_slot = entry["bag_enum"], entry["slot"]
				if _move_entry_to_slot(entry, target_bag, target_slot, bag_states):
					slot_to_id.pop((src_bag, src_slot), None)
					slot_to_id[(target_bag, target_slot)] = item_id
					total_api_calls += 1
					plan_moves_done += 1
				pending.discard(item_id)
				made_progress = True

		if not made_progress:
			# Deadlock: all remaining items are in a mutual-wait cycle.
			# Break it by moving one item to a free buffer slot.
			broke = False
			for item_id in list(pending):
				if max_moves is not None and total_api_calls >= max_moves:
					break
				entry = entry_by_id.get(item_id)
				if entry is None:
					pending.discard(item_id)
					continue
				free_bag, free_slot = _find_any_free_slot(bag_states, available_storage_bags)
				if free_bag is None:
					break
				src_bag, src_slot = entry["bag_enum"], entry["slot"]
				if _move_entry_to_slot(entry, free_bag, free_slot, bag_states):
					slot_to_id.pop((src_bag, src_slot), None)
					slot_to_id[(free_bag, free_slot)] = item_id
					total_api_calls += 1
					broke = True
				break
			if not broke:
				break  # Truly stuck — no free slots

	return plan_moves_done, len(pending) == 0


def _get_sort_priority(entry, allowed_by_bag, allowed_models_by_bag):
	"""Return a sort key for a wrong entry in the placement queue.

	Items from a filtered (non-wildcard) source pane sort first (priority 0) because they
	need a specific destination. Wildcard-source items sort last (priority 1).
	"""
	allowed_types = allowed_by_bag.get(entry["bag_enum"], [])
	allowed_model_ids = allowed_models_by_bag.get(entry["bag_enum"], [])
	is_filtered_source = not _storage_allows_all_types(allowed_types)
	is_filtered_model_source = not _storage_allows_all_model_ids(allowed_model_ids)
	return 0 if (is_filtered_source or is_filtered_model_source) else 1


def _build_wrong_entries(
	entries,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
	available_storage_bags=None,
):
	"""Collect and sort all entries that are not in the correct storage pane."""
	wrong_entries = []
	for entry in entries:
		if _is_entry_excluded_from_regular_sort(entry):
			continue

		is_wrong = not _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		)

		if is_wrong:
			wrong_entries.append(entry)
	wrong_entries.sort(
		key=lambda entry: _get_sort_priority(
			entry,
			allowed_by_bag,
			allowed_models_by_bag,
		)
	)
	return wrong_entries


def _is_item_allowed_in_storage(
	item_type_name: str,
	model_id: int,
	bag_enum,
	allowed_by_bag,
	allowed_models_by_bag,
	ignore_type_filter: bool = False,
):
	"""Return True when the item passes the filters of the given pane.

	Set ignore_type_filter=True to check only the model-ID filter (used when model priority applies).
	"""
	allowed_types = allowed_by_bag.get(bag_enum, [])
	allowed_model_ids = allowed_models_by_bag.get(bag_enum, [])
	if ignore_type_filter:
		return _is_item_model_id_allowed(model_id, allowed_model_ids)
	return _matches_storage_rules(item_type_name, model_id, allowed_types, allowed_model_ids)


def _try_move_wrong_entry(
	entry,
	available_storage_bags,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
	wildcard_bags,
	wildcard_model_bags,
	bag_states,
	dry_run: bool = False,
):
	"""Try to move a misplaced item into the best available target pane.

	Priority ranking: model-ID match > type match > wildcard.
	Target panes must rank equal or higher than the source pane.
	Returns True when the item was successfully moved.
	"""
	type_name = entry["type_name"]
	model_id = int(entry.get("model_id", 0))
	source_bag = entry["bag_enum"]
	if source_bag == Bags.MaterialStorage:
		return False

	target_model_bags = filtered_bags_by_model_id.get(model_id, [])
	has_model_priority = len(target_model_bags) > 0

	def _classify_bag_priority(bag_enum):
		if has_model_priority and bag_enum in target_model_bags and _is_item_allowed_in_storage(
			type_name,
			model_id,
			bag_enum,
			allowed_by_bag,
			allowed_models_by_bag,
			True,
		):
			if bag_enum in filtered_bags_by_type.get(type_name, []):
				return 3, 1, "modelid>itemtype"
			return 3, 0, "modelid"

		if not _is_item_allowed_in_storage(type_name, model_id, bag_enum, allowed_by_bag, allowed_models_by_bag):
			return 0, 0, "none"

		if bag_enum in filtered_bags_by_type.get(type_name, []):
			return 2, 0, "itemtype"

		if bag_enum in wildcard_bags:
			return 1, 0, "all"

		return 1, 0, "all"

	source_rank, _, _ = _classify_bag_priority(source_bag)
	candidate_targets = []
	for bag_enum in available_storage_bags:
		if bag_enum == source_bag:
			continue
		if bag_enum == Bags.MaterialStorage:
			continue

		rank, bonus, reason_label = _classify_bag_priority(bag_enum)
		if rank < source_rank:
			continue
		if rank == source_rank:
			continue

		candidate_targets.append((rank, bonus, bag_enum, reason_label))

	candidate_targets.sort(key=lambda item: (item[0], item[1]), reverse=True)

	for _, _, candidate_bag, reason_label in candidate_targets:
		next_slot = _get_next_free_slot(bag_states, candidate_bag)
		if next_slot is None:
			continue
		source_slot_before = int(entry.get("slot", 0))
		if _move_entry_to_slot(entry, candidate_bag, next_slot, bag_states, dry_run=dry_run):
			_debug_log(
				f"Move reason={reason_label} | item={entry['item_id']} modelid={model_id} type={type_name} | from {source_bag.value}:{source_slot_before + 1} -> {candidate_bag.value}:{next_slot + 1}"
			)
			return True

	return False


def _update_sort_progress_state(task):
	"""Recompute _sort_progress_ratio and _sort_progress_text from the current task state."""
	global _sort_progress_ratio
	global _sort_progress_text

	phase = task.get("phase", "placement")
	if phase == "stack":
		_sort_progress_ratio = 0.05
		_sort_progress_text = "Sorting (stack merge): running..."
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	if phase == "materials":
		total_candidates = max(int(task.get("material_total", 0)), 1)
		processed_candidates = min(int(task.get("material_index", 0)), total_candidates)
		material_ratio = float(processed_candidates) / float(total_candidates)
		material_ratio = max(0.0, min(1.0, material_ratio))
		_sort_progress_ratio = 0.05 * material_ratio
		_sort_progress_text = f"Sorting (material deposit): {material_ratio * 100.0:.1f}%"
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	if phase == "plan":
		_sort_progress_ratio = 0.2
		_sort_progress_text = "Planning moves..."
		return

	if phase == "execute":
		ex_total = max(int(task.get("execute_total", 1)), 1)
		ex_done = min(int(task.get("execute_done", 0)), ex_total)
		ex_ratio = max(0.0, min(1.0, float(ex_done) / float(ex_total)))
		_sort_progress_ratio = 0.2 + ex_ratio * 0.8
		_sort_progress_text = f"Executing moves: {ex_done}/{ex_total}"
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	_sort_progress_ratio = 1.0
	_sort_progress_text = "Done"


def _start_sort_task(available_storage_bags):
	"""Initialise a new asynchronous sort task that will be processed frame by frame.

	Builds the full sort context (entries, bag states, filter maps) and sets the initial
	phase to 'stack' (or skips directly into 'materials' if AUTO_DEPOSIT_MATERIALS is on).
	Does nothing if a sort task is already running.
	"""
	global _sort_task_state
	global _sort_done_until

	if _sort_task_state is not None:
		return
	_sort_done_until = 0.0  # clear any lingering post-sort display

	(
		allowed_by_bag,
		allowed_models_by_bag,
		filtered_bags_by_type,
		filtered_bags_by_model_id,
		wildcard_bags,
		wildcard_model_bags,
	) = _build_allowed_type_map(available_storage_bags)
	entries, bag_states = _collect_storage_item_entries(available_storage_bags)

	_sort_task_state = {
		"available_storage_bags": list(available_storage_bags),
		"allowed_by_bag": allowed_by_bag,
		"allowed_models_by_bag": allowed_models_by_bag,
		"filtered_bags_by_type": filtered_bags_by_type,
		"filtered_bags_by_model_id": filtered_bags_by_model_id,
		"wildcard_bags": wildcard_bags,
		"wildcard_model_bags": wildcard_model_bags,
		"entries": entries,
		"bag_states": bag_states,
		"stack_merge_actions": 0,
		"moved_items": 0,
		"wrong_entries": [],
		"wrong_index": 0,
		"moved_this_pass": 0,
		"initial_wrong_count": 1,
		"current_wrong_count": 1,
		"remaining_wrong_count": 0,
		"retry_round": 0,
		"round_start_moved_items": 0,
		"model_sort_actions": 0,
		"unresolved_model_sort_bags": 0,
		"model_bag_index": 0,
		"compact_actions": 0,
		"compact_bag_index": 0,
		"next_move_time": 0.0,
		"next_move_delay": 0.0,
		"has_model_filters": _has_any_model_id_filters(available_storage_bags),
		"consolidate_to_back": CONSOLIDATE_TO_BACK,
		"consolidate_back_bag_index": 0,
		"consolidate_back_total": 1,
		"consolidate_back_actions": 0,
		"move_plan": {},
		"execute_done": 0,
		"execute_total": 1,
		"post_material_phase_done": False,
		"phase": "stack",
	}

	if AUTO_DEPOSIT_MATERIALS:
		_sort_task_state["material_actions"] = 0
		_sort_task_state["material_units_moved"] = 0
		_sort_task_state["material_skipped_full"] = 0
		_sort_task_state["material_skipped_no_slot"] = 0
		_sort_task_state["material_no_slot_models"] = {}
		_start_material_phase(_sort_task_state, available_storage_bags, "plan")

	_update_sort_progress_state(_sort_task_state)


def _get_sort_task_context(task):
	"""Build a compact context dictionary used by phase handlers."""
	return {
		"available_storage_bags": task["available_storage_bags"],
		"allowed_by_bag": task["allowed_by_bag"],
		"allowed_models_by_bag": task["allowed_models_by_bag"],
		"filtered_bags_by_type": task["filtered_bags_by_type"],
		"filtered_bags_by_model_id": task["filtered_bags_by_model_id"],
		"wildcard_bags": task["wildcard_bags"],
		"wildcard_model_bags": task["wildcard_model_bags"],
		"consolidate_to_back": task.get("consolidate_to_back", False),
		"entries": task["entries"],
		"bag_states": task["bag_states"],
	}


def _process_phase_stack(task, ctx):
	"""Run the stack-merge phase and initialize placement candidates."""
	if task["phase"] != "stack":
		return False

	task["stack_merge_actions"] = _consolidate_storage_stacks(
		ctx["entries"],
		ctx["bag_states"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
	)
	task["wrong_entries"] = _build_wrong_entries(
		ctx["entries"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
		ctx["available_storage_bags"],
	)
	task["initial_wrong_count"] = max(len(task["wrong_entries"]), 1)
	task["current_wrong_count"] = len(task["wrong_entries"])
	task["wrong_index"] = 0
	task["moved_this_pass"] = 0
	task["phase"] = "plan"
	_update_sort_progress_state(task)
	return True


def _process_phase_materials(task, ctx):
	"""Run one step of the material auto-deposit phase, including rescan passes."""
	if task["phase"] != "materials":
		return False

	material_candidates = task.get("material_candidates", [])
	material_index = int(task.get("material_index", 0))
	material_storage_by_model = task.get("material_storage_by_model", {})

	if material_index >= len(material_candidates):
		current_pass_index = int(task.get("material_pass_index", 0))
		moves_this_pass = int(task.get("material_moves_this_pass", 0))
		if moves_this_pass > 0 and current_pass_index < MATERIAL_MAX_RESCAN_PASSES:
			task["material_pass_index"] = current_pass_index + 1
			task["material_moves_this_pass"] = 0
			task["material_candidates"] = _collect_material_entries_for_deposit(ctx["available_storage_bags"])
			task["material_index"] = 0
			task["material_total"] = len(task["material_candidates"])
			task["material_storage_by_model"] = _get_material_storage_quantities_by_model()
		else:
			task["phase"] = str(task.get("material_resume_phase", "stack"))
		_update_sort_progress_state(task)
		return True

	steps_left = 1 if SLOW_MODE else max(SORT_STEPS_PER_FRAME, 1)
	while steps_left > 0 and task["phase"] == "materials":
		if task["material_index"] >= len(material_candidates):
			task["phase"] = "stack"
			break

		entry = material_candidates[task["material_index"]]
		task["material_index"] += 1
		steps_left -= 1

		item_id = int(entry.get("item_id", 0))
		model_id = int(entry.get("model_id", 0))
		if item_id <= 0 or model_id <= 0:
			continue

		current_qty = int(material_storage_by_model.get(model_id, 0))
		if current_qty >= MATERIAL_STACK_MAX:
			task["material_skipped_full"] = int(task.get("material_skipped_full", 0)) + 1
			continue

		moved_units = _deposit_material_to_material_storage(item_id, model_id, material_storage_by_model)
		if moved_units == -1:
			task["material_skipped_no_slot"] = int(task.get("material_skipped_no_slot", 0)) + 1
			no_slot_models = task.get("material_no_slot_models", {})
			no_slot_models[model_id] = int(no_slot_models.get(model_id, 0)) + 1
			task["material_no_slot_models"] = no_slot_models
			continue
		if moved_units <= 0:
			continue

		task["material_actions"] = int(task.get("material_actions", 0)) + 1
		task["material_units_moved"] = int(task.get("material_units_moved", 0)) + int(moved_units)
		task["material_moves_this_pass"] = int(task.get("material_moves_this_pass", 0)) + 1
		material_storage_by_model[model_id] = min(MATERIAL_STACK_MAX, int(material_storage_by_model.get(model_id, 0)) + int(moved_units))
		_set_sort_task_move_delay(task)
		break

	if task["phase"] == "materials":
		task["material_storage_by_model"] = material_storage_by_model
	_update_sort_progress_state(task)
	return True


def _process_phase_placement(task, ctx):
	"""Move wrongly placed items into better target panes according to filters."""
	if task["phase"] != "placement":
		return False

	steps_left = 1 if SLOW_MODE else max(SORT_STEPS_PER_FRAME, 1)
	while steps_left > 0 and task["phase"] == "placement":
		wrong_entries = task["wrong_entries"]
		if task["wrong_index"] >= len(wrong_entries):
			if task["moved_this_pass"] == 0:
				task["remaining_wrong_count"] = len(wrong_entries)
				task["phase"] = "model"
				break

			task["wrong_entries"] = _build_wrong_entries(
				ctx["entries"],
				ctx["allowed_by_bag"],
				ctx["allowed_models_by_bag"],
				ctx["filtered_bags_by_type"],
				ctx["filtered_bags_by_model_id"],
				ctx["available_storage_bags"],
			)
			task["current_wrong_count"] = len(task["wrong_entries"])
			task["wrong_index"] = 0
			task["moved_this_pass"] = 0
			if len(task["wrong_entries"]) == 0:
				task["remaining_wrong_count"] = 0
				task["phase"] = "model"
				break
			continue

		entry = wrong_entries[task["wrong_index"]]
		task["wrong_index"] += 1
		steps_left -= 1

		is_correct = _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			ctx["allowed_by_bag"],
			ctx["allowed_models_by_bag"],
			ctx["filtered_bags_by_type"],
			ctx["filtered_bags_by_model_id"],
		)
		if is_correct:
			continue

		if _try_move_wrong_entry(
			entry,
			ctx["available_storage_bags"],
			ctx["allowed_by_bag"],
			ctx["allowed_models_by_bag"],
			ctx["filtered_bags_by_type"],
			ctx["filtered_bags_by_model_id"],
			ctx["wildcard_bags"],
			ctx["wildcard_model_bags"],
			ctx["bag_states"],
		):
			task["moved_items"] += 1
			task["moved_this_pass"] += 1
			_set_sort_task_move_delay(task)
			break

	task["current_wrong_count"] = len(
		_build_wrong_entries(
			ctx["entries"],
			ctx["allowed_by_bag"],
			ctx["allowed_models_by_bag"],
			ctx["filtered_bags_by_type"],
			ctx["filtered_bags_by_model_id"],
			ctx["available_storage_bags"],
		)
	)
	_update_sort_progress_state(task)
	return True


def _process_phase_model(task, ctx):
	"""Sort items by model within each pane and perform optional retry rounds."""
	if task["phase"] != "model":
		return False

	if task["model_bag_index"] < len(ctx["available_storage_bags"]):
		bag_enum = ctx["available_storage_bags"][task["model_bag_index"]]
		max_model_moves = 1 if SLOW_MODE else None
		model_sort_actions, unresolved_model_sort_bags, completed_bag = _sort_items_within_storage_by_model_id(
			ctx["entries"],
			ctx["bag_states"],
			ctx["available_storage_bags"],
			[bag_enum],
			max_model_moves,
		)
		task["model_sort_actions"] += model_sort_actions
		if model_sort_actions > 0:
			_set_sort_task_move_delay(task)
		if completed_bag:
			task["unresolved_model_sort_bags"] += unresolved_model_sort_bags
			task["model_bag_index"] += 1
		_update_sort_progress_state(task)
		return True

	remaining_wrong_entries = _build_wrong_entries(
		ctx["entries"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
		ctx["available_storage_bags"],
	)
	task["remaining_wrong_count"] = len(remaining_wrong_entries)
	moved_in_round = int(task.get("moved_items", 0)) - int(task.get("round_start_moved_items", 0))
	can_retry = (
		task["remaining_wrong_count"] > 0
		and moved_in_round > 0
		and int(task.get("retry_round", 0)) < int(MAX_AUTO_SORT_RETRIES)
	)

	if can_retry:
		task["retry_round"] = int(task.get("retry_round", 0)) + 1
		task["wrong_entries"] = list(remaining_wrong_entries)
		task["initial_wrong_count"] = max(len(task["wrong_entries"]), 1)
		task["current_wrong_count"] = len(task["wrong_entries"])
		task["wrong_index"] = 0
		task["moved_this_pass"] = 0
		task["round_start_moved_items"] = int(task.get("moved_items", 0))
		task["phase"] = "placement"
		_debug_log(
			f"Auto-retry sort round {task['retry_round']}/{MAX_AUTO_SORT_RETRIES} (remaining incorrect: {task['remaining_wrong_count']})."
		)
		_update_sort_progress_state(task)
		return True

	task["phase"] = "compact"
	task["compact_bag_index"] = 0
	_update_sort_progress_state(task)
	return True


def _process_phase_compact(task, ctx):
	"""Compact slots per pane, then hand off to consolidate_back (if enabled) or finalize."""
	if task["phase"] != "compact":
		return False

	if task["compact_bag_index"] < len(ctx["available_storage_bags"]):
		bag_enum = ctx["available_storage_bags"][task["compact_bag_index"]]
		max_compact_moves = 1 if SLOW_MODE else None
		compact_actions, completed_bag = _compact_storage_slots(
			ctx["entries"],
			ctx["bag_states"],
			ctx["available_storage_bags"],
			[bag_enum],
			max_compact_moves,
		)
		task["compact_actions"] += compact_actions
		if compact_actions > 0:
			_set_sort_task_move_delay(task)
		if completed_bag:
			task["compact_bag_index"] += 1
		_update_sort_progress_state(task)
		return True

	# All bags compacted — decide next phase
	if ctx.get("consolidate_to_back", False):
		task["phase"] = "consolidate_back"
		# Pre-count how many consolidatable items are not already at their target positions
		task["consolidate_back_total"] = max(
			_count_consolidate_back_items(
				ctx["entries"],
				ctx["bag_states"],
				ctx["available_storage_bags"],
				ctx["allowed_by_bag"],
				ctx["allowed_models_by_bag"],
				ctx["filtered_bags_by_type"],
				ctx["filtered_bags_by_model_id"],
			),
			1,
		)
	elif AUTO_DEPOSIT_MATERIALS and not bool(task.get("post_material_phase_done", False)):
		task["post_material_phase_done"] = True
		_start_material_phase(task, ctx["available_storage_bags"], "finalize")
	else:
		task["phase"] = "finalize"
	_update_sort_progress_state(task)
	return True


def _process_phase_consolidate_back(task, ctx):
	"""Push items in all wildcard panes to the rear (treated as one combined space)."""
	if task["phase"] != "consolidate_back":
		return False

	# Always process 1 placement per frame so the progress bar visibly advances
	# even when only a few items need to be consolidated.
	max_cb_moves = 1
	cb_actions, completed = _consolidate_items_to_back(
		ctx["entries"],
		ctx["bag_states"],
		ctx["available_storage_bags"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
		max_cb_moves,
	)
	task["consolidate_back_actions"] += cb_actions
	if cb_actions > 0:
		_set_sort_task_move_delay(task)

	if completed:
		# Phase done — all items are in place (or couldn't be moved)
		if AUTO_DEPOSIT_MATERIALS and not bool(task.get("post_material_phase_done", False)):
			task["post_material_phase_done"] = True
			_start_material_phase(task, ctx["available_storage_bags"], "finalize")
		else:
			task["phase"] = "finalize"

	_update_sort_progress_state(task)
	return True


def _process_phase_plan(task, ctx):
	"""Simulate all sort phases (dry run) to compute the final position of every item.

	Runs entirely in one frame (no API calls). Stores the move plan in the task and
	transitions to the 'execute' phase.
	"""
	if task["phase"] != "plan":
		return False

	plan = _plan_sort_moves(
		ctx["entries"],
		ctx["bag_states"],
		ctx["available_storage_bags"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
		ctx["wildcard_bags"],
		ctx["wildcard_model_bags"],
		bool(task.get("consolidate_to_back", False)),
	)
	task["move_plan"] = plan
	task["execute_total"] = max(len(plan), 1)
	task["execute_done"] = 0
	task["phase"] = "execute"
	_debug_log(f"Move plan computed: {len(plan)} item(s) need to move.")
	_update_sort_progress_state(task)
	return True


def _process_phase_execute(task, ctx):
	"""Execute pre-planned moves frame by frame until all items reach their final positions."""
	if task["phase"] != "execute":
		return False

	max_exec_moves = 1 if SLOW_MODE else max(SORT_STEPS_PER_FRAME, 1)
	plan_done, completed = _execute_move_plan(
		ctx["entries"],
		ctx["bag_states"],
		task.get("move_plan", {}),
		ctx["available_storage_bags"],
		max_exec_moves,
	)
	task["execute_done"] = int(task.get("execute_done", 0)) + plan_done
	task["moved_items"] = int(task.get("moved_items", 0)) + plan_done
	if plan_done > 0:
		_set_sort_task_move_delay(task)

	if completed:
		if AUTO_DEPOSIT_MATERIALS and not bool(task.get("post_material_phase_done", False)):
			task["post_material_phase_done"] = True
			_start_material_phase(task, ctx["available_storage_bags"], "finalize")
		else:
			task["phase"] = "finalize"

	_update_sort_progress_state(task)
	return True


def _process_phase_finalize(task, ctx):
	"""Emit final warnings/debug summaries and complete the active sort task."""
	global _sort_task_state

	if task["phase"] != "finalize":
		return False

	bag_label_by_enum = {}
	for index, bag_enum in enumerate(ctx["available_storage_bags"], start=1):
		bag_label_by_enum[bag_enum] = _to_roman(index)

	remaining_wrong_entries = _build_wrong_entries(
		ctx["entries"],
		ctx["allowed_by_bag"],
		ctx["allowed_models_by_bag"],
		ctx["filtered_bags_by_type"],
		ctx["filtered_bags_by_model_id"],
		ctx["available_storage_bags"],
	)
	task["remaining_wrong_count"] = len(remaining_wrong_entries)

	if len(remaining_wrong_entries) > 0:
		for entry in remaining_wrong_entries:
			pane_label = bag_label_by_enum.get(entry["bag_enum"], str(entry["bag_enum"].value))
			slot_number = int(entry["slot"]) + 1
			ConsoleLog(
				MODULE_NAME,
				f"Incorrect placement: Pane {pane_label}, Slot {slot_number}, Type {entry['type_name']}, Quantity {entry['quantity']}, ItemID {entry['item_id']}",
				Console.MessageType.Warning,
			)
	else:
		_debug_log("All items are in the correct pane after sorting.")

	if AUTO_DEPOSIT_MATERIALS:
		remaining_material_entries = [
			entry
			for entry in _collect_material_entries_for_deposit(ctx["available_storage_bags"])
			if entry.get("bag_enum") != Bags.MaterialStorage
		]
		if len(remaining_material_entries) > 0:
			material_full = int(task.get("material_skipped_full", 0))
			material_no_slot = int(task.get("material_skipped_no_slot", 0))
			ConsoleLog(
				MODULE_NAME,
				f"Auto-Deposit Materials incomplete: {len(remaining_material_entries)} items still outside Material Storage (full={material_full}, no_slot={material_no_slot}).",
				Console.MessageType.Warning,
			)
			no_slot_models = task.get("material_no_slot_models", {})
			if len(no_slot_models) > 0:
				for model_id in sorted(no_slot_models.keys()):
					count = int(no_slot_models.get(model_id, 0))
					try:
						model_name = ModelID(int(model_id)).name
					except Exception:
						model_name = "Unknown"
					ConsoleLog(
						MODULE_NAME,
						f"Auto-Deposit no_slot model: {int(model_id)} ({model_name}) hits={count}",
						Console.MessageType.Warning,
					)

	if task["unresolved_model_sort_bags"] > 0 and task.get("has_model_filters", False):
		ConsoleLog(
			MODULE_NAME,
			f"Model-ID sorting incomplete in {task['unresolved_model_sort_bags']} storage tabs (no free slot/move failed).",
			Console.MessageType.Warning,
		)

	_debug_log(
		f"Sort queued moves: {task['moved_items']} | Stack merges: {task['stack_merge_actions']} | Model-ID sort moves: {task['model_sort_actions']} | Compact moves: {task['compact_actions']} | Consolidate-back moves: {task.get('consolidate_back_actions', 0)} | Incorrect remaining: {task['remaining_wrong_count']}"
	)

	task["phase"] = "done"
	_update_sort_progress_state(task)
	_sort_task_state = None
	# Keep the progress bar visible for 2 s after completion so the game
	# item animations are still visible while the bar shows "Done".
	_sort_done_until = time.monotonic() + 2.0
	# Force stats cache refresh so the progress bars reflect the post-sort state.
	global _cache_needs_refresh
	_cache_needs_refresh = True
	return True


def _process_sort_task():
	"""Main dispatcher that advances the active sort task by one phase step."""
	global _sort_task_state
	global _material_storage_quantities_live

	if _sort_task_state is None:
		return

	task = _sort_task_state
	ctx = _get_sort_task_context(task)

	if AUTO_DEPOSIT_MATERIALS:
		_material_storage_quantities_live = _get_material_storage_quantities_by_model()

	if _is_sort_task_waiting_for_delay(task):
		_update_sort_progress_state(task)
		return

	if _process_phase_stack(task, ctx):
		return
	if _process_phase_materials(task, ctx):
		return
	if _process_phase_plan(task, ctx):
		return
	if _process_phase_execute(task, ctx):
		return
	_process_phase_finalize(task, ctx)


def _calculate_correct_item_progress(available_storage_bags):
	"""Return (correct_items, total_items, ratio) for the current placement quality indicator."""
	(
		allowed_by_bag,
		allowed_models_by_bag,
		filtered_bags_by_type,
		filtered_bags_by_model_id,
		_,
		_,
	) = _build_allowed_type_map(available_storage_bags)
	entries, _ = _collect_storage_item_entries(available_storage_bags)

	total_items = len(entries)
	if total_items == 0:
		return 0, 0, 1.0

	correct_items = 0
	for entry in entries:
		if _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		):
			correct_items += 1

	ratio = float(correct_items) / float(total_items)
	return correct_items, total_items, ratio


def _sort_storage_items(available_storage_bags):
	"""Synchronous (blocking) sort — runs all phases to completion in a single call.

	Used as a fallback / legacy path. The async task system (_start_sort_task) is preferred
	for the interactive overlay since it spreads work across frames.
	Returns (moved_items, stack_merge_actions, remaining_wrong, model+compact_actions).
	"""
	(
		allowed_by_bag,
		allowed_models_by_bag,
		filtered_bags_by_type,
		filtered_bags_by_model_id,
		wildcard_bags,
		wildcard_model_bags,
	) = _build_allowed_type_map(available_storage_bags)
	entries, bag_states = _collect_storage_item_entries(available_storage_bags)
	stack_merge_actions = _consolidate_storage_stacks(
		entries,
		bag_states,
		allowed_by_bag,
		allowed_models_by_bag,
		filtered_bags_by_type,
		filtered_bags_by_model_id,
	)

	moved_items = 0

	def sort_priority(entry):
		return _get_sort_priority(entry, allowed_by_bag, allowed_models_by_bag)

	while True:
		wrong_entries = []
		for entry in entries:
			if not _is_item_in_correct_storage(
				entry["bag_enum"],
				entry["type_name"],
				entry.get("model_id", 0),
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
			):
				wrong_entries.append(entry)

		if len(wrong_entries) == 0:
			break

		wrong_entries.sort(key=sort_priority)
		moved_this_pass = 0

		for entry in wrong_entries:
			if _is_item_in_correct_storage(
				entry["bag_enum"],
				entry["type_name"],
				entry.get("model_id", 0),
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
			):
				continue

			if not _try_move_wrong_entry(
				entry,
				available_storage_bags,
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
				wildcard_bags,
				wildcard_model_bags,
				bag_states,
			):
				continue
			moved_items += 1
			moved_this_pass += 1

		if moved_this_pass == 0:
			break

	bag_label_by_enum = {}
	for index, bag_enum in enumerate(available_storage_bags, start=1):
		bag_label_by_enum[bag_enum] = _to_roman(index)

	remaining_wrong_entries = []
	for entry in entries:
		if not _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		):
			remaining_wrong_entries.append(entry)

	if len(remaining_wrong_entries) > 0:
		for entry in remaining_wrong_entries:
			pane_label = bag_label_by_enum.get(entry["bag_enum"], str(entry["bag_enum"].value))
			slot_number = int(entry["slot"]) + 1
			ConsoleLog(
				MODULE_NAME,
				f"Incorrect placement: Pane {pane_label}, Slot {slot_number}, Type {entry['type_name']}, Quantity {entry['quantity']}, ItemID {entry['item_id']}",
				Console.MessageType.Warning,
			)
	else:
		_debug_log("All items are in the correct pane after sorting.")

	model_sort_actions, unresolved_model_sort_bags, _ = _sort_items_within_storage_by_model_id(
		entries,
		bag_states,
		available_storage_bags,
	)
	compact_actions, _ = _compact_storage_slots(
		entries,
		bag_states,
		available_storage_bags,
	)
	if unresolved_model_sort_bags > 0 and _has_any_model_id_filters(available_storage_bags):
		ConsoleLog(
			MODULE_NAME,
			f"Model-ID sorting incomplete in {unresolved_model_sort_bags} storage tabs (no free slot/move failed).",
			Console.MessageType.Warning,
		)

	return moved_items, stack_merge_actions, len(remaining_wrong_entries), model_sort_actions + compact_actions


def _get_available_storage_bags(anniversary_slot_unlocked: bool):
	"""Return the list of storage pane enums that are actually available in the current session.

	Panes are probed in order (Storage1–Storage13, optionally Storage14).
	The last pane is excluded when anniversary_slot_unlocked is False.
	"""
	bag_order = [
		Bags.Storage1,
		Bags.Storage2,
		Bags.Storage3,
		Bags.Storage4,
		Bags.Storage5,
		Bags.Storage6,
		Bags.Storage7,
		Bags.Storage8,
		Bags.Storage9,
		Bags.Storage10,
		Bags.Storage11,
		Bags.Storage12,
		Bags.Storage13,
	]

	if anniversary_slot_unlocked:
		bag_order.append(Bags.Storage14)

	available_bags = []
	for bag_enum in bag_order:
		info = _get_storage_bag_info(bag_enum)
		if info["available"]:
			available_bags.append(bag_enum)

	if not anniversary_slot_unlocked and len(available_bags) > 0:
		available_bags.pop()

	return available_bags


def _get_storage_bag_info(bag_enum):
	"""Return a dict with availability, used slot count, total size, and free slot count for a pane."""
	try:
		bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
		size = bag.GetSize()
		used = bag.GetItemCount() if size > 0 else 0
		free = max(size - used, 0)
		return {
			"available": size > 0,
			"used": used,
			"size": size,
			"free": free,
		}
	except Exception:
		return {
			"available": False,
			"used": 0,
			"size": 0,
			"free": 0,
		}


def _get_slot_item_type_rows(bag_enum, allowed_types=None):
	"""Return a list of (slot_number, type_name, quantity, is_allowed) tuples for the pane's items.

	Used to populate the per-pane slot breakdown in the settings panel.
	"""
	if allowed_types is None:
		allowed_types = []

	rows = []
	try:
		bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
		for item in bag.GetItems():
			if not item or item.item_id == 0:
				continue

			model_id = _get_item_model_id(item)
			type_id, type_name = GLOBAL_CACHE.Item.GetItemType(item.item_id)
			if not type_name:
				type_name = f"Type {type_id}"
			type_name = _resolve_item_type_name(item.item_id, type_name, model_id)
			is_allowed = not allowed_types or type_name in allowed_types

			slot_number = int(item.slot) + 1
			quantity = _get_item_quantity(item)
			rows.append((slot_number, type_name, quantity, is_allowed))

		rows.sort(key=lambda entry: entry[0])
		return rows
	except Exception:
		return []

def _get_storage_anchor_position(anchor_window_width=None):
	"""Calculate the screen position where our overlay window should be anchored.

	Frame IDs are resolved once per session (expensive: JSON file read + hash lookups)
	and stored permanently.  GetFrameCoords / FrameExists run every frame — they are
	fast GW memory reads with no file I/O, so the position is always pixel-perfect.
	"""
	global _anchor_cached_frame_id, _anchor_cached_fallback_frame_id, _anchor_frame_ids_resolved

	if anchor_window_width is None:
		anchor_window_width = max(float(_last_window_width), float(COMPACT_WINDOW_MIN_WIDTH))
	else:
		anchor_window_width = max(float(anchor_window_width), 1.0)

	# One-time resolution of frame IDs (JSON read + hash lookup — done only once).
	if not _anchor_frame_ids_resolved:
		frame_id = 0
		try:
			frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "Xunlai Window")
		except Exception:
			frame_id = 0
		if frame_id == 0:
			frame_id = UIManager.GetFrameIDByHash(XUNLAI_WINDOW_HASH)
		if frame_id == 0:
			frame_id = CHEST_FRAME_ID
		_anchor_cached_frame_id = frame_id
		try:
			_anchor_cached_fallback_frame_id = UIManager.GetFrameIDByHash(INVENTORY_FRAME_HASH)
		except Exception:
			_anchor_cached_fallback_frame_id = 0
		_anchor_frame_ids_resolved = True

	# GetFrameCoords / FrameExists are fast per-frame GW memory reads — no file I/O.
	if _anchor_cached_frame_id > 0 and UIManager.FrameExists(_anchor_cached_frame_id):
		try:
			left, top, right, bottom = UIManager.GetFrameCoords(_anchor_cached_frame_id)
			x1 = min(left, right)
			y1 = min(top, bottom)
			y2 = max(top, bottom)
			anchor_x = float(x1 - ANCHOR_OFFSET_X - anchor_window_width)
			anchor_y = float(y1 + ANCHOR_OFFSET_Y) if y2 > y1 else float(top + ANCHOR_OFFSET_Y)
			return anchor_x, anchor_y
		except Exception:
			pass

	if _anchor_cached_fallback_frame_id > 0 and UIManager.FrameExists(_anchor_cached_fallback_frame_id):
		try:
			left, top, right, _ = UIManager.GetFrameCoords(_anchor_cached_fallback_frame_id)
			if right > left:
				return float(left - ANCHOR_OFFSET_X - anchor_window_width), float(top + ANCHOR_OFFSET_Y)
		except Exception:
			pass

	return None


# -----------------------------------------------------------------------------
# UI rendering and interactions
# -----------------------------------------------------------------------------
def _draw_storage_hover_modelid_tooltip(available_storage_bags):
	"""Show an ImGui tooltip with type and model info when hovering over a storage item."""
	try:
		hovered_item_id = int(GLOBAL_CACHE.Inventory.GetHoveredItemID())
	except Exception:
		return

	if hovered_item_id <= 0:
		return

	for bag_index, bag_enum in enumerate(available_storage_bags, start=1):
		try:
			bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
			items = bag.GetItems()
		except Exception:
			continue

		for item in items:
			if not item or int(item.item_id) != hovered_item_id:
				continue

			try:
				model_id = int(item.model_id) if hasattr(item, "model_id") else int(GLOBAL_CACHE.Item.GetModelID(hovered_item_id))
			except Exception:
				model_id = 0

			try:
				type_id, type_name = GLOBAL_CACHE.Item.GetItemType(hovered_item_id)
				if not type_name:
					type_name = f"Type {type_id}"
				resolved_type_name = _resolve_item_type_name(hovered_item_id, type_name, model_id)
			except Exception:
				resolved_type_name = "Unknown"

			if PyImGui.begin_tooltip():
				PyImGui.text(f"ModelID: {model_id}")
				PyImGui.text(f"Type: {resolved_type_name}")
				PyImGui.end_tooltip()
			return


def _draw_toggle_icon_window():
	"""Draw the 40×40 frameless icon button that toggles the main Xunlai Manager panel."""
	global WINDOW_OPEN

	icon_window_size = 40.0
	anchor_pos = _get_storage_anchor_position(icon_window_size)
	if anchor_pos is not None:
		PyImGui.set_next_window_pos(anchor_pos[0] + 60.0, anchor_pos[1] + 55.0)
	PyImGui.set_next_window_size(icon_window_size, icon_window_size)

	icon_window_flags = (
		PyImGui.WindowFlags.NoTitleBar
		| PyImGui.WindowFlags.NoResize
		| PyImGui.WindowFlags.NoScrollbar
		| PyImGui.WindowFlags.NoCollapse
		| PyImGui.WindowFlags.NoBackground
	)
	PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
	if PyImGui.begin("##XunlaiManagerToggle", icon_window_flags):
		icon_path = MODULE_ICON
		absolute_icon_path = os.path.join(project_root, MODULE_ICON)
		if os.path.exists(absolute_icon_path):
			icon_path = absolute_icon_path

		icon_size = 36.0
		icon_offset = (icon_window_size - icon_size) / 2.0
		cursor_x, cursor_y = PyImGui.get_cursor_screen_pos()
		draw_pos = (cursor_x + icon_offset, cursor_y + icon_offset)
		try:
			ImGui.DrawTextureInDrawList(draw_pos, (icon_size, icon_size), icon_path)
		except Exception:
			PyImGui.set_cursor_screen_pos(draw_pos[0] + 6.0, draw_pos[1] + 8.0)
			PyImGui.text("CM")

		PyImGui.set_cursor_screen_pos(cursor_x, cursor_y)
		clicked_toggle = PyImGui.invisible_button("##XunlaiManagerToggleButton", icon_window_size, icon_window_size)

		if clicked_toggle:
			WINDOW_OPEN = not WINDOW_OPEN
			ini_handler.write_key(INI_KEY, "window_open", WINDOW_OPEN)
		if PyImGui.is_item_hovered():
			if PyImGui.begin_tooltip():
				PyImGui.text("Open Xunlai Manager" if not WINDOW_OPEN else "Hide Xunlai Manager")
				PyImGui.end_tooltip()
	PyImGui.end()
	PyImGui.pop_style_var(1)


def _draw_window():
	"""Main per-frame render function: draws the toggle icon and the full GUI when WINDOW_OPEN is True."""
	global ANNIVERSARY_SLOT_UNLOCKED
	global _last_saved_anniversary_slot_unlocked
	global SHOW_SETTINGS
	global SHOW_DEBUG
	global SLOW_MODE
	global CONSOLIDATE_TO_BACK
	global AUTO_DEPOSIT_MATERIALS
	global WINDOW_OPEN
	global _sort_task_state
	global _sort_progress_ratio
	global _sort_progress_text
	global _sort_done_until
	global _selected_settings_account
	global _last_window_width
	global _idle_refresh_timer
	global _cache_needs_refresh
	global _cached_available_bags
	global _cached_bag_infos
	global _cached_tabs_total_used
	global _cached_tabs_total_size
	global _cached_correct_items
	global _cached_total_items
	global _cached_correct_ratio

	if not GLOBAL_CACHE.Inventory.IsStorageOpen():
		return

	_ensure_account_settings_loaded()

	_draw_toggle_icon_window()

	if _sort_task_state is not None and not WINDOW_OPEN:
		_process_sort_task()

	if not WINDOW_OPEN:
		return

	window_flags = PyImGui.WindowFlags.AlwaysAutoResize
	if not SHOW_SETTINGS:
		PyImGui.set_next_window_size(COMPACT_WINDOW_MIN_WIDTH, COMPACT_WINDOW_MIN_HEIGHT)
	anchor_pos = _get_storage_anchor_position()
	if anchor_pos is not None and not SHOW_SETTINGS:
		PyImGui.set_next_window_pos(anchor_pos[0], anchor_pos[1])
		window_flags |= PyImGui.WindowFlags.NoMove

	if not PyImGui.begin(MODULE_NAME, True, window_flags):
		PyImGui.end()
		return



	#PyImGui.separator()

	previous_show_settings = SHOW_SETTINGS
	SHOW_SETTINGS = PyImGui.checkbox("Show Settings", SHOW_SETTINGS)
	if SHOW_SETTINGS != previous_show_settings:
		ini_handler.write_key(INI_KEY, "show_settings", SHOW_SETTINGS)

	if SHOW_SETTINGS:
		previous_show_debug = SHOW_DEBUG
		SHOW_DEBUG = PyImGui.checkbox("Show Debug", SHOW_DEBUG)
		if SHOW_DEBUG != previous_show_debug:
			ini_handler.write_key(INI_KEY, "show_debug", SHOW_DEBUG)

		ANNIVERSARY_SLOT_UNLOCKED = PyImGui.checkbox("Anniversary slot unlocked", ANNIVERSARY_SLOT_UNLOCKED)
		if ANNIVERSARY_SLOT_UNLOCKED != _last_saved_anniversary_slot_unlocked and save_timer.IsExpired():
			ini_handler.write_key(INI_KEY, "anniversary_slot_unlocked", ANNIVERSARY_SLOT_UNLOCKED)
			_last_saved_anniversary_slot_unlocked = ANNIVERSARY_SLOT_UNLOCKED
			save_timer.Reset()
			_cache_needs_refresh = True  # available bags depend on anniversary unlock

		previous_slow_mode = SLOW_MODE
		SLOW_MODE = PyImGui.checkbox("Slow Mode", SLOW_MODE)
		if SLOW_MODE != previous_slow_mode:
			ini_handler.write_key(INI_KEY, "slow_mode", SLOW_MODE)

		previous_consolidate_to_back = CONSOLIDATE_TO_BACK
		CONSOLIDATE_TO_BACK = PyImGui.checkbox("Autosort unfiltered items", CONSOLIDATE_TO_BACK)
		if CONSOLIDATE_TO_BACK != previous_consolidate_to_back:
			ini_handler.write_key(INI_KEY, "consolidate_to_back", CONSOLIDATE_TO_BACK)

		previous_auto_deposit_materials = AUTO_DEPOSIT_MATERIALS
		AUTO_DEPOSIT_MATERIALS = PyImGui.checkbox("Auto-Deposit Materials", AUTO_DEPOSIT_MATERIALS)
		if AUTO_DEPOSIT_MATERIALS != previous_auto_deposit_materials:
			ini_handler.write_key(INI_KEY, "auto_deposit_materials", AUTO_DEPOSIT_MATERIALS)

	# Refresh expensive storage stats at most once every 2 s (or immediately when flagged).
	if _cache_needs_refresh or _idle_refresh_timer.IsExpired():
		_cached_available_bags = _get_available_storage_bags(ANNIVERSARY_SLOT_UNLOCKED)
		_cached_bag_infos = []
		_cached_tabs_total_used = 0
		_cached_tabs_total_size = 0
		for _ce_bag in _cached_available_bags:
			_ce_info = _get_storage_bag_info(_ce_bag)
			_cached_bag_infos.append((_ce_bag, _ce_info))
			_cached_tabs_total_used += _ce_info["used"]
			_cached_tabs_total_size += _ce_info["size"]
		_cached_correct_items, _cached_total_items, _cached_correct_ratio = _calculate_correct_item_progress(_cached_available_bags)
		_idle_refresh_timer.Reset()
		_cache_needs_refresh = False
	available_storage_bags = _cached_available_bags
	_draw_storage_hover_modelid_tooltip(available_storage_bags)
	if _sort_task_state is None:
		if PyImGui.button("Sort"):
			_start_sort_task(available_storage_bags)
		if SHOW_DEBUG:
			PyImGui.same_line(0, 8)
			if PyImGui.button("Read MaterialStorage"):
				_log_material_storage_counts_to_console()
	else:
		PyImGui.begin_disabled(True)
		PyImGui.button("Sort")
		if SHOW_DEBUG:
			PyImGui.same_line(0, 8)
			PyImGui.button("Read MaterialStorage")
		PyImGui.end_disabled()

	if _sort_task_state is not None:
		_process_sort_task()

	PyImGui.separator()

	if len(available_storage_bags) == 0:
		PyImGui.text("No storage panes available")
		PyImGui.end()
		return

	bag_infos = _cached_bag_infos
	tabs_total_used = _cached_tabs_total_used
	tabs_total_size = _cached_tabs_total_size

	tabs_used_ratio = (float(tabs_total_used) / float(tabs_total_size)) if tabs_total_size > 0 else 0.0
	PyImGui.text("Overall (all tabs):")
	PyImGui.progress_bar(tabs_used_ratio, -1, 0, f"{tabs_used_ratio * 100.0:.1f}% Full ({tabs_total_used}/{tabs_total_size})")
	correct_items, total_items, correct_ratio = _cached_correct_items, _cached_total_items, _cached_correct_ratio
	PyImGui.progress_bar(correct_ratio, -1, 0, f"{correct_ratio * 100.0:.1f}% Sorted ({correct_items}/{total_items})")
	if _sort_task_state is not None or time.monotonic() < _sort_done_until:
		progress_text = _sort_progress_text if _sort_progress_text else "Sortiere..."
		PyImGui.progress_bar(_sort_progress_ratio, -1, 0, f"{_sort_progress_ratio * 100.0:.1f}% {progress_text}")

	if SHOW_DEBUG and AUTO_DEPOSIT_MATERIALS:
		if _sort_task_state is not None:
			material_done = int(_sort_task_state.get("material_index", 0))
			material_total = int(_sort_task_state.get("material_total", 0))
			material_actions = int(_sort_task_state.get("material_actions", 0))
			material_units = int(_sort_task_state.get("material_units_moved", 0))
			material_full = int(_sort_task_state.get("material_skipped_full", 0))
			material_no_slot = int(_sort_task_state.get("material_skipped_no_slot", 0))
			PyImGui.text(f"Material deposit: {material_done}/{material_total} checked | Moves: {material_actions} | Units: {material_units}")
			PyImGui.text(f"Material skips: full={material_full} | no_slot={material_no_slot}")
		else:
			PyImGui.text("Material deposit: idle")
	PyImGui.separator()

	if SHOW_SETTINGS:
		runtime_account = _sanitize_path_component(_get_current_account_email())
		loaded_account = _sanitize_path_component(_active_account_email)

		account_options = _list_settings_accounts()
		if len(account_options) > 0:
			if _selected_settings_account not in account_options:
				_selected_settings_account = loaded_account if loaded_account in account_options else account_options[0]
			selected_index = account_options.index(_selected_settings_account)
			selected_index = PyImGui.combo("Load settings from this account", selected_index, account_options)
			selected_index = max(0, min(selected_index, len(account_options) - 1))
			_selected_settings_account = account_options[selected_index]

			if PyImGui.button("Load"):
				_copy_account_settings_to_current(_selected_settings_account, runtime_account)
				_ensure_account_settings_loaded(force=True)

		PyImGui.separator()

		if PyImGui.begin_tab_bar("##XunlaiStorageTabs"):
			for index, (bag_enum, info) in enumerate(bag_infos, start=1):
				tab_label = _to_roman(index)
				if PyImGui.begin_tab_item(tab_label):


					allowed_types = _load_allowed_types_for_storage(bag_enum)
					allowed_model_ids = _load_allowed_model_ids_for_storage(bag_enum)
					bag_key = bag_enum.value
					selected_entry_kind = _selected_allowed_entry_kind_by_storage.get(bag_key, "type")
					PyImGui.text("Allowed item types:")

					if PyImGui.begin_child(f"AllowedTypesList##{bag_key}", (0, 120), True, PyImGui.WindowFlags.NoFlag):
						if len(allowed_types) == 0 and len(allowed_model_ids) == 0:
							PyImGui.text("None selected (all allowed)")
						else:
							selected_idx = _selected_allowed_type_idx_by_storage.get(bag_key, 0)
							for list_index, type_name in enumerate(allowed_types):
								is_selected = selected_entry_kind == "type" and list_index == selected_idx
								if PyImGui.selectable(
									f"{type_name.replace('_', ' ')}##allowed_{bag_key}_{list_index}",
									is_selected,
									PyImGui.SelectableFlags.NoFlag,
									(0.0, 0.0),
								):
									_selected_allowed_type_idx_by_storage[bag_key] = list_index
									_selected_allowed_entry_kind_by_storage[bag_key] = "type"

						if len(allowed_model_ids) > 0:
							if len(allowed_types) > 0:
								PyImGui.separator()
							selected_model_idx = _selected_allowed_model_id_idx_by_storage.get(bag_key, 0)
							for list_index, model_id in enumerate(allowed_model_ids):
								is_selected = selected_entry_kind == "model" and list_index == selected_model_idx
								if PyImGui.selectable(
									f"modelid({model_id})##allowed_model_inline_{bag_key}_{list_index}",
									is_selected,
									PyImGui.SelectableFlags.NoFlag,
									(0.0, 0.0),
								):
									_selected_allowed_model_id_idx_by_storage[bag_key] = list_index
									_selected_allowed_entry_kind_by_storage[bag_key] = "model"
					PyImGui.end_child()

					combo_idx = _selected_add_type_idx_by_storage.get(bag_key, 0)
					combo_labels = [t.replace("_", " ") for t in ITEM_TYPE_OPTIONS]
					combo_idx = PyImGui.combo(f"Add item type##combo_{bag_key}", combo_idx, combo_labels)
					_selected_add_type_idx_by_storage[bag_key] = combo_idx

					if PyImGui.button(f"Add##add_{bag_key}"):
						selected_type = ITEM_TYPE_OPTIONS[combo_idx]
						if selected_type not in allowed_types:
							allowed_types.append(selected_type)
							_save_allowed_types_for_storage(bag_enum)

					selected_entry_kind = _selected_allowed_entry_kind_by_storage.get(bag_key, "type")
					can_remove_type = selected_entry_kind == "type" and len(allowed_types) > 0
					can_remove_model = selected_entry_kind == "model" and len(allowed_model_ids) > 0
					can_remove = can_remove_type or can_remove_model
					if not can_remove:
						PyImGui.begin_disabled(True)
					if PyImGui.button(f"Remove##remove_{bag_key}") and can_remove:
						if can_remove_type:
							selected_idx = _selected_allowed_type_idx_by_storage.get(bag_key, 0)
							selected_idx = max(0, min(selected_idx, len(allowed_types) - 1))
							allowed_types.pop(selected_idx)
							if len(allowed_types) == 0:
								_selected_allowed_type_idx_by_storage[bag_key] = 0
								if len(allowed_model_ids) > 0:
									_selected_allowed_entry_kind_by_storage[bag_key] = "model"
							else:
								_selected_allowed_type_idx_by_storage[bag_key] = min(selected_idx, len(allowed_types) - 1)
							_save_allowed_types_for_storage(bag_enum)
						else:
							selected_model_idx = _selected_allowed_model_id_idx_by_storage.get(bag_key, 0)
							selected_model_idx = max(0, min(selected_model_idx, len(allowed_model_ids) - 1))
							allowed_model_ids.pop(selected_model_idx)
							if len(allowed_model_ids) == 0:
								_selected_allowed_model_id_idx_by_storage[bag_key] = 0
								if len(allowed_types) > 0:
									_selected_allowed_entry_kind_by_storage[bag_key] = "type"
							else:
								_selected_allowed_model_id_idx_by_storage[bag_key] = min(selected_model_idx, len(allowed_model_ids) - 1)
							_save_allowed_model_ids_for_storage(bag_enum)
					if not can_remove:
						PyImGui.end_disabled()

					PyImGui.separator()
					PyImGui.text("Allowed model IDs:")

					model_input = _model_id_input_by_storage.get(bag_key, 0)
					model_input = PyImGui.input_int(f"Model ID##model_input_{bag_key}", int(model_input))
					if model_input < 0:
						model_input = 0
					_model_id_input_by_storage[bag_key] = int(model_input)

					if PyImGui.button(f"Add Model ID##add_model_{bag_key}"):
						model_id_to_add = int(_model_id_input_by_storage.get(bag_key, 0))
						if model_id_to_add > 0 and model_id_to_add not in allowed_model_ids:
							allowed_model_ids.append(model_id_to_add)
							allowed_model_ids.sort()
							_save_allowed_model_ids_for_storage(bag_enum)
					PyImGui.end_tab_item()
			PyImGui.end_tab_bar()

		PyImGui.separator()
		if PyImGui.button("Close Settings"):
			SHOW_SETTINGS = False
			ini_handler.write_key(INI_KEY, "show_settings", SHOW_SETTINGS)

	window_size = PyImGui.get_window_size()
	if isinstance(window_size, (tuple, list)) and len(window_size) >= 2:
		try:
			_last_window_width = max(float(window_size[0]), 1.0)
		except Exception:
			pass

	PyImGui.end()


def main():
	try:
		_draw_window()
	except Exception as e:
		ConsoleLog(MODULE_NAME, f"Error in main: {str(e)}", Console.MessageType.Error)


if __name__ == "__main__":
	main()
