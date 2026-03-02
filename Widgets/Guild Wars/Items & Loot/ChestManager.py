import PyInventory
import PyImGui
import random
import time
import os
import re
import shutil

from Py4GWCoreLib import *


MODULE_NAME = "Chest Manager"
MODULE_ICON = "Textures/Module_Icons/TeamInventoryViewer.png"
CHEST_FRAME_ID = 752
XUNLAI_WINDOW_HASH = 2315448754
FRAME_ALIAS_FILE = ".\\Py4GWCoreLib\\frame_aliases.json"
INVENTORY_FRAME_HASH = 291586130
ANCHOR_OFFSET_X = 6
ANCHOR_OFFSET_Y = 0
COMPACT_WINDOW_MIN_WIDTH = 200
COMPACT_WINDOW_MIN_HEIGHT = 230

ANNIVERSARY_SLOT_UNLOCKED = False
SHOW_SETTINGS = False
SHOW_DEBUG = False
SLOW_MODE = False
TRY_EMPTY_FIRST_STORAGE = False
INI_KEY = "Chest Manager"
INI_RELATIVE_PATH = "Settings/{account}/Inventory/ChestManager/chest_manager.ini"


project_root = Py4GW.Console.get_projects_path()
save_timer = ThrottledTimer(500)
ini_handler = None
_active_account_email = ""
_active_ini_path = ""
_last_saved_anniversary_slot_unlocked = False
_selected_settings_account = ""
_last_window_width = float(COMPACT_WINDOW_MIN_WIDTH)

_allowed_types_by_storage = {}
_selected_allowed_type_idx_by_storage = {}
_selected_add_type_idx_by_storage = {}
_allowed_model_ids_by_storage = {}
_selected_allowed_model_id_idx_by_storage = {}
_model_id_input_by_storage = {}
_selected_allowed_entry_kind_by_storage = {}

SORT_STEPS_PER_FRAME = 8
MAX_AUTO_SORT_RETRIES = 3
_sort_task_state = None
_sort_progress_ratio = 0.0
_sort_progress_text = ""


def _sanitize_path_component(value: str) -> str:
	if not value:
		return "default_settings"
	return re.sub(r'[\\/:*?"<>|]+', "_", value).strip() or "default_settings"


def _get_current_account_email() -> str:
	try:
		account_email = Player.GetAccountEmail()
		if account_email:
			return str(account_email)
	except Exception:
		pass
	return "default_settings"


def _build_account_ini_path(account_email: str) -> str:
	safe_account = _sanitize_path_component(account_email)
	relative_path = INI_RELATIVE_PATH.format(account=safe_account)
	return os.path.join(project_root, relative_path)


def _ensure_ini_path_exists(ini_path: str):
	parent_dir = os.path.dirname(ini_path)
	if parent_dir:
		os.makedirs(parent_dir, exist_ok=True)
	if not os.path.exists(ini_path):
		with open(ini_path, "w", encoding="utf-8"):
			pass


def _clear_storage_settings_cache():
	_allowed_types_by_storage.clear()
	_selected_allowed_type_idx_by_storage.clear()
	_selected_add_type_idx_by_storage.clear()
	_allowed_model_ids_by_storage.clear()
	_selected_allowed_model_id_idx_by_storage.clear()
	_model_id_input_by_storage.clear()
	_selected_allowed_entry_kind_by_storage.clear()


def _list_settings_accounts() -> list:
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
	global ini_handler
	global _active_account_email
	global _active_ini_path
	global ANNIVERSARY_SLOT_UNLOCKED
	global _last_saved_anniversary_slot_unlocked
	global SHOW_SETTINGS
	global SHOW_DEBUG
	global SLOW_MODE
	global TRY_EMPTY_FIRST_STORAGE
	global _sort_task_state
	global _selected_settings_account

	runtime_account_email = _get_current_account_email()
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
	TRY_EMPTY_FIRST_STORAGE = ini_handler.read_bool(INI_KEY, "try_empty_first_storage", False)
	_sort_task_state = None
	_clear_storage_settings_cache()


_ensure_account_settings_loaded(force=True)


def _debug_log(message: str):
	if not SHOW_DEBUG:
		return
	ConsoleLog(MODULE_NAME, message, Console.MessageType.Info)


def _set_sort_task_move_delay(task):
	if not SLOW_MODE:
		task["next_move_time"] = 0.0
		task["next_move_delay"] = 0.0
		return
	delay_seconds = random.uniform(0.8, 1.0)
	task["next_move_time"] = time.monotonic() + delay_seconds
	task["next_move_delay"] = delay_seconds


def _is_sort_task_waiting_for_delay(task) -> bool:
	if not SLOW_MODE:
		return False
	return time.monotonic() < float(task.get("next_move_time", 0.0))


def _get_sort_task_delay_remaining(task) -> float:
	return max(float(task.get("next_move_time", 0.0)) - time.monotonic(), 0.0)

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


def _build_default_pcons_model_ids():
	model_names = [
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
	]

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


DEFAULT_PCONS_MODEL_IDS = _build_default_pcons_model_ids()


def _build_model_id_set_from_names(model_names):
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


def _build_summoning_stone_model_ids():
	model_names = [
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
	]

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


SUMMONING_STONE_MODEL_IDS = _build_summoning_stone_model_ids()


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
	if type_name == "Pcon":
		return "Pcons"
	if type_name in WEAPON_TYPE_NAMES:
		return "Weapons"
	if type_name in ARMOR_TYPE_NAMES:
		return "Armor"
	return type_name


def _is_default_pcons_item(item_id: int, model_id: int | None = None) -> bool:
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

	if len(candidate_ids) == 0:
		return False

	for candidate in candidate_ids:
		if candidate in DEFAULT_PCONS_MODEL_IDS:
			return True
	return False


def _is_summoning_stone_item(item_id: int, model_id: int | None = None) -> bool:
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

	if len(candidate_ids) == 0:
		return False

	for candidate in candidate_ids:
		if candidate in SUMMONING_STONE_MODEL_IDS:
			return True
	return False


def _is_model_in_set(item_id: int, model_id: int | None, model_set) -> bool:
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
	normalized = _normalize_item_type_name(raw_type_name)
	if normalized in ("Usable", "Pcons"):
		if _is_model_in_set(item_id, model_id, ALCOHOL_MODEL_IDS):
			return "Alcohol"
		if _is_model_in_set(item_id, model_id, SWEETS_MODEL_IDS):
			return "Sweets"
		if _is_model_in_set(item_id, model_id, PARTY_MODEL_IDS):
			return "Party"
	if _is_default_pcons_item(item_id, model_id):
		return "Pcons"
	if normalized == "Usable":
		if GLOBAL_CACHE.Item.Type.IsTome(item_id):
			return "Tome"
		if _is_summoning_stone_item(item_id, model_id):
			return "Summoning Stones"
	return normalized


def _build_item_type_options():
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


def _format_item_type_name(type_name: str) -> str:
	return type_name.replace("_", " ")


def _get_storage_allowed_types_key(bag_enum):
	return f"allowed_item_types_storage_{bag_enum.value}"


def _get_storage_allowed_model_ids_key(bag_enum):
	return f"allowed_model_ids_storage_{bag_enum.value}"


def _load_allowed_types_for_storage(bag_enum):
	bag_key = bag_enum.value
	if bag_key in _allowed_types_by_storage:
		return _allowed_types_by_storage[bag_key]

	raw = ini_handler.read_key(INI_KEY, _get_storage_allowed_types_key(bag_enum), "")
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
	bag_key = bag_enum.value
	if bag_key in _allowed_model_ids_by_storage:
		return _allowed_model_ids_by_storage[bag_key]

	raw = ini_handler.read_key(INI_KEY, _get_storage_allowed_model_ids_key(bag_enum), "")
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
	bag_key = bag_enum.value
	allowed = _allowed_types_by_storage.get(bag_key, [])
	ini_handler.write_key(INI_KEY, _get_storage_allowed_types_key(bag_enum), ",".join(allowed))


def _save_allowed_model_ids_for_storage(bag_enum):
	bag_key = bag_enum.value
	allowed = _allowed_model_ids_by_storage.get(bag_key, [])
	ini_handler.write_key(INI_KEY, _get_storage_allowed_model_ids_key(bag_enum), ",".join(str(model_id) for model_id in allowed))


def _has_any_model_id_filters(available_storage_bags) -> bool:
	for bag_enum in available_storage_bags:
		if len(_load_allowed_model_ids_for_storage(bag_enum)) > 0:
			return True
	return False


def _is_item_type_allowed(type_name: str, allowed_types) -> bool:
	if len(allowed_types) == 0:
		return True
	return type_name in allowed_types


def _is_item_model_id_allowed(model_id: int, allowed_model_ids) -> bool:
	if len(allowed_model_ids) == 0:
		return True
	return int(model_id) in allowed_model_ids


def _matches_storage_rules(item_type_name: str, model_id: int, allowed_types, allowed_model_ids) -> bool:
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
	if len(allowed_types) == 0:
		return True
	return len(set(allowed_types)) >= len(set(ITEM_TYPE_OPTIONS))


def _storage_allows_all_model_ids(allowed_model_ids) -> bool:
	return len(allowed_model_ids) == 0


def _storage_is_all_allowed(allowed_types, allowed_model_ids) -> bool:
	return _storage_allows_all_types(allowed_types) and _storage_allows_all_model_ids(allowed_model_ids)


def _build_allowed_type_map(available_storage_bags):
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


def _collect_storage_item_entries(available_storage_bags):
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

			model_id = int(item.model_id) if hasattr(item, "model_id") else 0
			type_id, type_name = GLOBAL_CACHE.Item.GetItemType(item.item_id)
			if not type_name:
				type_name = f"Type {type_id}"
			type_name = _resolve_item_type_name(item.item_id, type_name, model_id)

			slot = int(item.slot)
			occupied_slots.add(slot)
			quantity = int(item.quantity) if hasattr(item, "quantity") else 1
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


def _get_stack_merge_key(entry):
	if not entry.get("is_stackable", False):
		return None
	return (entry.get("model_id", 0), entry.get("dye_key", None))


def _consolidate_storage_stacks(
	entries,
	bag_states,
	allowed_by_bag,
	allowed_models_by_bag,
	filtered_bags_by_type,
	filtered_bags_by_model_id,
):
	max_stack_size = 250
	moved_actions = 0
	protected_item_ids = set()

	for entry in entries:
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
		if entry.get("quantity", 0) <= 0:
			continue
		merge_key = _get_stack_merge_key(entry)
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
	state = bag_states.get(bag_enum)
	if not state:
		return None
	if len(state["free_slots"]) == 0:
		return None
	return state["free_slots"][0]


def _reserve_move_in_state(bag_states, source_bag_enum, source_slot: int, target_bag_enum, target_slot: int):
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


def _move_entry_to_slot(entry, target_bag_enum, target_slot: int, bag_states) -> bool:
	source_bag = entry["bag_enum"]
	source_slot = entry["slot"]
	if source_bag == target_bag_enum and source_slot == target_slot:
		return True

	try:
		GLOBAL_CACHE.Inventory.MoveItem(entry["item_id"], target_bag_enum.value, target_slot, entry["quantity"])
	except Exception:
		return False

	_reserve_move_in_state(bag_states, source_bag, source_slot, target_bag_enum, target_slot)
	entry["bag_enum"] = target_bag_enum
	entry["slot"] = target_slot
	return True


def _get_model_sort_type_priority(type_name: str):
	try:
		return ITEM_TYPE_OPTIONS.index(type_name), type_name
	except ValueError:
		return len(ITEM_TYPE_OPTIONS), type_name


def _sort_items_within_storage_by_model_id(entries, bag_states, available_storage_bags, target_bags=None, max_move_actions=None):
	move_actions = 0
	unresolved_bags = 0
	completed_all_bags = True
	bags_to_process = target_bags if target_bags is not None else available_storage_bags

	for bag_enum in bags_to_process:
		bag_entries = [entry for entry in entries if entry.get("bag_enum") == bag_enum and entry.get("quantity", 0) > 0]
		if len(bag_entries) <= 1:
			continue

		target_slots = sorted(entry["slot"] for entry in bag_entries)
		desired_entries = sorted(
			bag_entries,
			key=lambda entry: (
				_get_model_sort_type_priority(str(entry.get("type_name", "")))[0],
				_get_model_sort_type_priority(str(entry.get("type_name", "")))[1],
				int(entry.get("model_id", 0)),
				int(entry.get("item_id", 0)),
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

				if not _move_entry_to_slot(occupant, bag_enum, free_slot, bag_states):
					continue

				moved_occupant = True
				slot_to_entry.pop(occupant_original_slot, None)
				slot_to_entry[free_slot] = occupant
				move_actions += 1

			source_bag_before = desired_entry["bag_enum"]
			source_slot_before = desired_entry["slot"]
			if not _move_entry_to_slot(desired_entry, bag_enum, target_slot, bag_states):
				if moved_occupant:
					if _move_entry_to_slot(occupant, bag_enum, occupant_original_slot, bag_states):
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


def _compact_storage_slots(entries, bag_states, available_storage_bags, target_bags=None, max_move_actions=None):
	move_actions = 0
	completed_all_bags = True
	bags_to_process = target_bags if target_bags is not None else available_storage_bags

	for bag_enum in bags_to_process:
		bag_entries = [entry for entry in entries if entry.get("bag_enum") == bag_enum and entry.get("quantity", 0) > 0]
		if len(bag_entries) <= 1:
			continue

		bag_entries.sort(key=lambda entry: int(entry.get("slot", 0)))
		for compact_slot, entry in enumerate(bag_entries):
			current_slot = int(entry.get("slot", 0))
			if current_slot == compact_slot:
				continue

			if not _move_entry_to_slot(entry, bag_enum, compact_slot, bag_states):
				continue

			move_actions += 1
			if max_move_actions is not None and move_actions >= max_move_actions:
				completed_all_bags = False
				return move_actions, completed_all_bags

	return move_actions, completed_all_bags


def _get_sort_priority(entry, allowed_by_bag, allowed_models_by_bag, first_storage_bag=None, try_empty_first=False):
	if try_empty_first and first_storage_bag is not None and entry["bag_enum"] == first_storage_bag:
		return -1
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
	try_empty_first=False,
):
	wrong_entries = []
	first_storage_bag = available_storage_bags[0] if available_storage_bags and len(available_storage_bags) > 0 else None
	for entry in entries:
		is_wrong = not _is_item_in_correct_storage(
			entry["bag_enum"],
			entry["type_name"],
			entry.get("model_id", 0),
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		)

		if (
			not is_wrong
			and try_empty_first
			and first_storage_bag is not None
			and entry["bag_enum"] == first_storage_bag
		):
			is_wrong = True

		if is_wrong:
			wrong_entries.append(entry)
	wrong_entries.sort(
		key=lambda entry: _get_sort_priority(
			entry,
			allowed_by_bag,
			allowed_models_by_bag,
			first_storage_bag,
			try_empty_first,
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
	try_empty_first=False,
):
	type_name = entry["type_name"]
	model_id = int(entry.get("model_id", 0))
	source_bag = entry["bag_enum"]
	first_storage_bag = available_storage_bags[0] if len(available_storage_bags) > 0 else None
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
		if try_empty_first and first_storage_bag is not None and bag_enum == first_storage_bag and source_bag != first_storage_bag:
			continue

		rank, bonus, reason_label = _classify_bag_priority(bag_enum)
		allow_equal_rank = (
			try_empty_first
			and first_storage_bag is not None
			and source_bag == first_storage_bag
			and rank > 0
		)
		if rank < source_rank:
			continue
		if rank == source_rank and not allow_equal_rank:
			continue

		candidate_targets.append((rank, bonus, bag_enum, reason_label))

	candidate_targets.sort(key=lambda item: (item[0], item[1]), reverse=True)

	for _, _, candidate_bag, reason_label in candidate_targets:
		next_slot = _get_next_free_slot(bag_states, candidate_bag)
		if next_slot is None:
			continue
		source_slot_before = int(entry.get("slot", 0))
		if _move_entry_to_slot(entry, candidate_bag, next_slot, bag_states):
			_debug_log(
				f"Move reason={reason_label} | item={entry['item_id']} modelid={model_id} type={type_name} | from {source_bag.value}:{source_slot_before + 1} -> {candidate_bag.value}:{next_slot + 1}"
			)
			return True

	return False


def _update_sort_progress_state(task):
	global _sort_progress_ratio
	global _sort_progress_text

	phase = task.get("phase", "placement")
	if phase == "stack":
		_sort_progress_ratio = 0.05
		_sort_progress_text = "Sorting (stack merge): running..."
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	if phase == "placement":
		initial_wrong_count = max(int(task.get("initial_wrong_count", 1)), 1)
		current_wrong_count = max(int(task.get("current_wrong_count", 0)), 0)
		placement_ratio = 1.0 - (float(current_wrong_count) / float(initial_wrong_count))
		placement_ratio = max(0.0, min(1.0, placement_ratio))
		_sort_progress_ratio = 0.2 + (placement_ratio * 0.6)
		_sort_progress_text = f"Sorting (types): {placement_ratio * 100.0:.1f}%"
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	if phase == "model":
		total_bags = max(len(task.get("available_storage_bags", [])), 1)
		processed_bags = min(int(task.get("model_bag_index", 0)), total_bags)
		model_ratio = float(processed_bags) / float(total_bags)
		model_ratio = max(0.0, min(1.0, model_ratio))
		_sort_progress_ratio = 0.8 + (model_ratio * 0.2)
		_sort_progress_text = f"Sorting (model ID): {model_ratio * 100.0:.1f}%"
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	if phase == "compact":
		total_bags = max(len(task.get("available_storage_bags", [])), 1)
		processed_bags = min(int(task.get("compact_bag_index", 0)), total_bags)
		compact_ratio = float(processed_bags) / float(total_bags)
		compact_ratio = max(0.0, min(1.0, compact_ratio))
		_sort_progress_ratio = 0.95 + (compact_ratio * 0.05)
		_sort_progress_text = f"Sorting (compact slots): {compact_ratio * 100.0:.1f}%"
		if _is_sort_task_waiting_for_delay(task):
			_sort_progress_text = f"{_sort_progress_text} | Pause: {_get_sort_task_delay_remaining(task):.1f}s"
		return

	_sort_progress_ratio = 1.0
	_sort_progress_text = "Done"


def _start_sort_task(available_storage_bags):
	global _sort_task_state

	if _sort_task_state is not None:
		return

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
		"try_empty_first": TRY_EMPTY_FIRST_STORAGE,
		"phase": "stack",
	}

	_update_sort_progress_state(_sort_task_state)


def _process_sort_task():
	global _sort_task_state

	if _sort_task_state is None:
		return

	task = _sort_task_state
	available_storage_bags = task["available_storage_bags"]
	allowed_by_bag = task["allowed_by_bag"]
	allowed_models_by_bag = task["allowed_models_by_bag"]
	filtered_bags_by_type = task["filtered_bags_by_type"]
	filtered_bags_by_model_id = task["filtered_bags_by_model_id"]
	wildcard_bags = task["wildcard_bags"]
	wildcard_model_bags = task["wildcard_model_bags"]
	try_empty_first = task.get("try_empty_first", False)
	entries = task["entries"]
	bag_states = task["bag_states"]

	if _is_sort_task_waiting_for_delay(task):
		_update_sort_progress_state(task)
		return

	if task["phase"] == "stack":
		task["stack_merge_actions"] = _consolidate_storage_stacks(
			entries,
			bag_states,
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
		)
		task["wrong_entries"] = _build_wrong_entries(
			entries,
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
			available_storage_bags,
			try_empty_first,
		)
		task["initial_wrong_count"] = max(len(task["wrong_entries"]), 1)
		task["current_wrong_count"] = len(task["wrong_entries"])
		task["wrong_index"] = 0
		task["moved_this_pass"] = 0
		task["phase"] = "placement" if len(task["wrong_entries"]) > 0 else "model"
		_update_sort_progress_state(task)
		return

	if task["phase"] == "placement":
		steps_left = 1 if SLOW_MODE else max(SORT_STEPS_PER_FRAME, 1)
		while steps_left > 0 and task["phase"] == "placement":
			wrong_entries = task["wrong_entries"]
			if task["wrong_index"] >= len(wrong_entries):
				if task["moved_this_pass"] == 0:
					task["remaining_wrong_count"] = len(wrong_entries)
					task["phase"] = "model"
					break

				task["wrong_entries"] = _build_wrong_entries(
					entries,
					allowed_by_bag,
					allowed_models_by_bag,
					filtered_bags_by_type,
					filtered_bags_by_model_id,
					available_storage_bags,
					try_empty_first,
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
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
			)
			if is_correct and not (try_empty_first and len(available_storage_bags) > 0 and entry["bag_enum"] == available_storage_bags[0]):
				continue

			if _try_move_wrong_entry(
				entry,
				available_storage_bags,
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
				wildcard_bags,
				wildcard_model_bags,
				bag_states,
				try_empty_first,
			):
				task["moved_items"] += 1
				task["moved_this_pass"] += 1
				_set_sort_task_move_delay(task)
				break

		task["current_wrong_count"] = len(
			_build_wrong_entries(
				entries,
				allowed_by_bag,
				allowed_models_by_bag,
				filtered_bags_by_type,
				filtered_bags_by_model_id,
				available_storage_bags,
				try_empty_first,
			)
		)
		_update_sort_progress_state(task)
		return

	if task["phase"] == "model":
		if task["model_bag_index"] < len(available_storage_bags):
			bag_enum = available_storage_bags[task["model_bag_index"]]
			max_model_moves = 1 if SLOW_MODE else None
			model_sort_actions, unresolved_model_sort_bags, completed_bag = _sort_items_within_storage_by_model_id(
				entries,
				bag_states,
				available_storage_bags,
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
			return

		bag_label_by_enum = {}
		for index, bag_enum in enumerate(available_storage_bags, start=1):
			bag_label_by_enum[bag_enum] = _to_roman(index)

		remaining_wrong_entries = _build_wrong_entries(
			entries,
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
			available_storage_bags,
			False,
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
			return

		task["phase"] = "compact"
		task["compact_bag_index"] = 0
		_update_sort_progress_state(task)
		return

	if task["phase"] == "compact":
		if task["compact_bag_index"] < len(available_storage_bags):
			bag_enum = available_storage_bags[task["compact_bag_index"]]
			max_compact_moves = 1 if SLOW_MODE else None
			compact_actions, completed_bag = _compact_storage_slots(
				entries,
				bag_states,
				available_storage_bags,
				[bag_enum],
				max_compact_moves,
			)
			task["compact_actions"] += compact_actions
			if compact_actions > 0:
				_set_sort_task_move_delay(task)
			if completed_bag:
				task["compact_bag_index"] += 1
			_update_sort_progress_state(task)
			return

		bag_label_by_enum = {}
		for index, bag_enum in enumerate(available_storage_bags, start=1):
			bag_label_by_enum[bag_enum] = _to_roman(index)

		remaining_wrong_entries = _build_wrong_entries(
			entries,
			allowed_by_bag,
			allowed_models_by_bag,
			filtered_bags_by_type,
			filtered_bags_by_model_id,
			available_storage_bags,
			False,
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

		if task["unresolved_model_sort_bags"] > 0 and task.get("has_model_filters", False):
			ConsoleLog(
				MODULE_NAME,
				f"Model-ID sorting incomplete in {task['unresolved_model_sort_bags']} storage tabs (no free slot/move failed).",
				Console.MessageType.Warning,
			)

		_debug_log(
			f"Sort queued moves: {task['moved_items']} | Stack merges: {task['stack_merge_actions']} | Model-ID sort moves: {task['model_sort_actions']} | Compact moves: {task['compact_actions']} | Incorrect remaining: {task['remaining_wrong_count']}"
		)

		task["phase"] = "done"
		_update_sort_progress_state(task)
		_sort_task_state = None
		return


def _calculate_correct_item_progress(available_storage_bags):
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
	if allowed_types is None:
		allowed_types = []

	rows = []
	try:
		bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
		for item in bag.GetItems():
			if not item or item.item_id == 0:
				continue

			model_id = int(item.model_id) if hasattr(item, "model_id") else 0
			type_id, type_name = GLOBAL_CACHE.Item.GetItemType(item.item_id)
			if not type_name:
				type_name = f"Type {type_id}"
			type_name = _resolve_item_type_name(item.item_id, type_name, model_id)
			is_allowed = _is_item_type_allowed(type_name, allowed_types)

			slot_number = int(item.slot) + 1
			quantity = int(item.quantity) if hasattr(item, "quantity") else 1
			rows.append((slot_number, type_name, quantity, is_allowed))

		rows.sort(key=lambda entry: entry[0])
		return rows
	except Exception:
		return []

def _get_storage_anchor_position():
	anchor_window_width = max(float(_last_window_width), float(COMPACT_WINDOW_MIN_WIDTH))
	frame_id = 0

	try:
		frame_id = UIManager.GetFrameIDByCustomLabel(FRAME_ALIAS_FILE, "Xunlai Window")
	except Exception:
		frame_id = 0

	if frame_id == 0:
		frame_id = UIManager.GetFrameIDByHash(XUNLAI_WINDOW_HASH)

	if frame_id == 0:
		frame_id = CHEST_FRAME_ID

	if frame_id > 0 and UIManager.FrameExists(frame_id):
		left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
		x1 = min(left, right)
		y1 = min(top, bottom)
		y2 = max(top, bottom)

		anchor_x = float(x1 - ANCHOR_OFFSET_X - anchor_window_width)

		if y2 > y1:
			anchor_y = float(y1 + ANCHOR_OFFSET_Y)
		else:
			anchor_y = float(top + ANCHOR_OFFSET_Y)

		return anchor_x, anchor_y

	fallback_frame_id = UIManager.GetFrameIDByHash(INVENTORY_FRAME_HASH)
	if fallback_frame_id == 0 or not UIManager.FrameExists(fallback_frame_id):
		return None

	left, top, right, _ = UIManager.GetFrameCoords(fallback_frame_id)
	if right <= left:
		return None

	return float(left - ANCHOR_OFFSET_X - anchor_window_width), float(top + ANCHOR_OFFSET_Y)


def _draw_window():
	global ANNIVERSARY_SLOT_UNLOCKED
	global _last_saved_anniversary_slot_unlocked
	global SHOW_SETTINGS
	global SHOW_DEBUG
	global SLOW_MODE
	global TRY_EMPTY_FIRST_STORAGE
	global _sort_task_state
	global _sort_progress_ratio
	global _sort_progress_text
	global _selected_settings_account
	global _last_window_width

	_ensure_account_settings_loaded()

	if not GLOBAL_CACHE.Inventory.IsStorageOpen():
		return

	window_flags = PyImGui.WindowFlags.AlwaysAutoResize
	if not SHOW_SETTINGS:
		PyImGui.set_next_window_size(COMPACT_WINDOW_MIN_WIDTH, COMPACT_WINDOW_MIN_HEIGHT)
	anchor_pos = _get_storage_anchor_position()
	if anchor_pos is not None:
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

		previous_slow_mode = SLOW_MODE
		SLOW_MODE = PyImGui.checkbox("Slow Mode", SLOW_MODE)
		if SLOW_MODE != previous_slow_mode:
			ini_handler.write_key(INI_KEY, "slow_mode", SLOW_MODE)

		previous_try_empty_first = TRY_EMPTY_FIRST_STORAGE
		TRY_EMPTY_FIRST_STORAGE = PyImGui.checkbox("Try to empty first storage", TRY_EMPTY_FIRST_STORAGE)
		if TRY_EMPTY_FIRST_STORAGE != previous_try_empty_first:
			ini_handler.write_key(INI_KEY, "try_empty_first_storage", TRY_EMPTY_FIRST_STORAGE)

	available_storage_bags = _get_available_storage_bags(ANNIVERSARY_SLOT_UNLOCKED)
	if _sort_task_state is None:
		if PyImGui.button("Sort"):
			_start_sort_task(available_storage_bags)
	else:
		PyImGui.begin_disabled(True)
		PyImGui.button("Sort")
		PyImGui.end_disabled()

	if _sort_task_state is not None:
		_process_sort_task()

	PyImGui.separator()

	if len(available_storage_bags) == 0:
		PyImGui.text("No storage panes available")
		PyImGui.end()
		return

	bag_infos = []
	tabs_total_used = 0
	tabs_total_size = 0
	for bag_enum in available_storage_bags:
		info = _get_storage_bag_info(bag_enum)
		bag_infos.append((bag_enum, info))
		tabs_total_used += info["used"]
		tabs_total_size += info["size"]

	tabs_used_ratio = (float(tabs_total_used) / float(tabs_total_size)) if tabs_total_size > 0 else 0.0
	PyImGui.text("Overall (all tabs):")
	PyImGui.progress_bar(tabs_used_ratio, -1, 0, f"{tabs_used_ratio * 100.0:.1f}% Full ({tabs_total_used}/{tabs_total_size})")
	correct_items, total_items, correct_ratio = _calculate_correct_item_progress(available_storage_bags)
	PyImGui.progress_bar(correct_ratio, -1, 0, f"{correct_ratio * 100.0:.1f}% Sorted ({correct_items}/{total_items})")
	if _sort_task_state is not None:
		progress_text = _sort_progress_text if _sort_progress_text else "Sortiere..."
		PyImGui.progress_bar(_sort_progress_ratio, -1, 0, f"{_sort_progress_ratio * 100.0:.1f}% {progress_text}")
	PyImGui.separator()

	if SHOW_SETTINGS:
		runtime_account = _sanitize_path_component(_get_current_account_email())
		loaded_account = _sanitize_path_component(_active_account_email)

		account_options = _list_settings_accounts()
		if len(account_options) > 0:
			if _selected_settings_account not in account_options:
				_selected_settings_account = loaded_account if loaded_account in account_options else account_options[0]
			selected_index = account_options.index(_selected_settings_account)
			selected_index = PyImGui.combo("Settings account", selected_index, account_options)
			selected_index = max(0, min(selected_index, len(account_options) - 1))
			_selected_settings_account = account_options[selected_index]

			if PyImGui.button("Load settings account"):
				_copy_account_settings_to_current(_selected_settings_account, runtime_account)
				_ensure_account_settings_loaded(force=True)

		PyImGui.separator()

		if PyImGui.begin_tab_bar("##ChestStorageTabs"):
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
									f"{_format_item_type_name(type_name)}##allowed_{bag_key}_{list_index}",
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
					combo_labels = [_format_item_type_name(type_name) for type_name in ITEM_TYPE_OPTIONS]
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
