from __future__ import annotations

import re
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple, TYPE_CHECKING
import importlib
import sys

import PyImGui
import Py4GW

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Color, Range, Player
from HeroAI.custom_skill import CustomSkillClass
from HeroAI.custom_skill_src.skill_types import CastConditions, SkillNature
from HeroAI.types import Skilltarget, SkillType

if TYPE_CHECKING:
	from HeroAI.custom_skill_src.skill_types import CustomSkill as _CustomSkill

# Runtime placeholder; replaced during rebind. Kept to satisfy type checkers without hard import failures.
CustomSkill: Any = None

if TYPE_CHECKING:
	from HeroAI.custom_skill_src.skill_types import CustomSkill as _CustomSkill

MODULE_NAME = "HeroAI Skill Editor"

window_module = ImGui.WindowModule(
	MODULE_NAME,
	window_name="HeroAI Skillbar",
	window_size=(1200, 700),
	window_flags=PyImGui.WindowFlags(PyImGui.WindowFlags.AlwaysAutoResize | PyImGui.WindowFlags.NoCollapse),
	can_close=False,
)

custom_skill_provider = CustomSkillClass()
_default_conditions = CastConditions()
DEFAULT_CONDITION_VALUES = {name: deepcopy(value) for name, value in vars(_default_conditions).items()}

ICON_SIZE = 40
EPSILON = 1e-5

PERCENT_FIELDS = {"LessLife", "MoreLife", "LessEnergy", "Overcast", "SacrificeHealth"}
AREA_FIELDS = {"EnemiesInRangeArea", "AlliesInRangeArea", "SpiritsInRangeArea", "MinionsInRangeArea"}
COUNTER_FIELDS = {"EnemiesInRange", "AlliesInRange", "SpiritsInRange", "MinionsInRange"}
LIST_FIELDS = {"WeaponSpellList", "EnchantmentList", "HexList", "ChantList", "CastingSkillList", "SharedEffects"}

_TARGET_OPTIONS: tuple[Skilltarget, ...] = tuple(sorted(Skilltarget, key=lambda option: option.value))
_SKILLTYPE_OPTIONS: tuple[SkillType, ...] = tuple(sorted(SkillType, key=lambda option: option.value))
_NATURE_OPTIONS: tuple[SkillNature, ...] = tuple(sorted(SkillNature, key=lambda option: option.value))
_NATURE_DESCRIPTIONS: dict[SkillNature, str] = {
	SkillNature.Offensive: "General offensive pressure or damage.",
	SkillNature.Enchantment_Removal: "Removes enemy enchantments.",
	SkillNature.Healing: "Restores health to allies or self.",
	SkillNature.Hex_Removal: "Removes hexes from allies.",
	SkillNature.Condi_Cleanse: "Cleanses conditions from allies; prioritize debuff removal.",
	SkillNature.Buff: "Provides beneficial buffs/boons to allies or self.",
	SkillNature.EnergyBuff: "Restores or boosts ally energy.",
	SkillNature.Neutral: "Utility effect with no strict offensive/defensive bias.",
	SkillNature.SelfTargeted: "Self-only effect; ignores external target selection.",
	SkillNature.Resurrection: "Revives defeated allies.",
	SkillNature.Interrupt: "Interrupts enemy skills or casts.",
	SkillNature.CustomA: "Custom bucket A for bespoke logic.",
	SkillNature.CustomB: "Custom bucket B for bespoke logic.",
	SkillNature.CustomC: "Custom bucket C for bespoke logic.",
	SkillNature.CustomD: "Custom bucket D for bespoke logic.",
	SkillNature.CustomE: "Custom bucket E for bespoke logic.",
	SkillNature.CustomF: "Custom bucket F for bespoke logic.",
	SkillNature.CustomG: "Custom bucket G for bespoke logic.",
	SkillNature.CustomH: "Custom bucket H for bespoke logic.",
	SkillNature.CustomI: "Custom bucket I for bespoke logic.",
	SkillNature.CustomJ: "Custom bucket J for bespoke logic.",
	SkillNature.CustomK: "Custom bucket K for bespoke logic.",
	SkillNature.CustomL: "Custom bucket L for bespoke logic.",
	SkillNature.CustomM: "Custom bucket M for bespoke logic.",
	SkillNature.CustomN: "Custom bucket N for bespoke logic.",
	SkillNature.OffensiveA: "Offensive bucket A (custom priority splitting).",
	SkillNature.OffensiveB: "Offensive bucket B (custom priority splitting).",
	SkillNature.OffensiveC: "Offensive bucket C (custom priority splitting).",
}
_SKILLTYPE_DESCRIPTIONS: dict[SkillType, str] = {
	SkillType.Bounty: "Temporary bounty effect granting bonus rewards.",
	SkillType.Scroll: "Scroll-type consumable effects.",
	SkillType.Stance: "Stances that alter behavior until they end.",
	SkillType.Hex: "Hex spells applied to enemies.",
	SkillType.Spell: "Standard spell cast with activation and aftercast.",
	SkillType.Enchantment: "Positive enchantment on self or allies.",
	SkillType.Signet: "Signets (no energy cost, activation time only).",
	SkillType.Condition: "Applies or interacts with conditions.",
	SkillType.Well: "Well placed on ground with area effect.",
	SkillType.Skill: "General skill without specific subtype.",
	SkillType.Ward: "Ward placed on ground providing area bonuses.",
	SkillType.Glyph: "Glyph that modifies the next cast(s).",
	SkillType.Title: "Title-related passive/active effects.",
	SkillType.Attack: "Attack skills augmenting weapon strikes.",
	SkillType.Shout: "Instant shout/command effects.",
	SkillType.Skill2: "Secondary general skill bucket.",
	SkillType.Passive: "Always-on passive effect.",
	SkillType.Environmental: "Environmental effect (map-based).",
	SkillType.Preparation: "Ranger preparations affecting next attacks.",
	SkillType.PetAttack: "Pet attack skills.",
	SkillType.Trap: "Ground trap armed after a delay.",
	SkillType.Ritual: "Binding rituals / spirit summons.",
	SkillType.EnvironmentalTrap: "Map environmental trap effects.",
	SkillType.ItemSpell: "Item spell granted by carried item.",
	SkillType.WeaponSpell: "Weapon spell applied to an ally's weapon.",
	SkillType.Form: "Dervish form that replaces skills temporarily.",
	SkillType.Chant: "Paragon chant affecting allies.",
	SkillType.EchoRefrain: "Paragon echo/refrain upkeep effects.",
	SkillType.Disguise: "Temporary disguise state/effect.",
}

_RANGE_DESCRIPTIONS: dict[Range, str] = {
	Range.Touch: "Touch range (~144 units): melee contact range.",
	Range.Adjacent: "Adjacent (~166 units): right next to you.",
	Range.Nearby: "Nearby (~252 units): short radius around you.",
	Range.Area: "Area (~322 units): moderate AoE radius.",
	Range.Earshot: "Earshot (~1012 units): shout/party-wide in aggro.",
	Range.Spellcast: "Spellcast (~1248 units): long spell range.",
	Range.Spirit: "Spirit (~2500 units): spirit interaction range.",
	Range.SafeCompass: "Safe compass (~4800 units): full compass padding.",
	Range.Compass: "Compass (~5000 units): entire compass radius.",
}
_CONDITION_OPTIONS: tuple[str, ...] = tuple(sorted(DEFAULT_CONDITION_VALUES.keys(), key=lambda name: name.lower()))
_ACTIVE_STATE_COLOR = (0.3, 0.9, 0.4, 1.0)

EDIT_POPUP_TARGET_COLUMN_WIDTH = 300
EDIT_POPUP_CONDITION_COLUMN_WIDTH = 500
TARGET_LIST_TARGET_WIDTH = 150
TARGET_LIST_ACTIVE_WIDTH = 50
TARGET_LIST_ACTION_WIDTH = 70
CONDITION_LIST_NAME_WIDTH = 150
CONDITION_LIST_VALUE_WIDTH = 70
CONDITION_LIST_CONTROL_WIDTH = 140
CONDITION_LIST_APPLY_WIDTH = 100


class SkillSourceLocation:
	__slots__ = ("path", "skill_name")

	def __init__(self, path: Path, skill_name: str) -> None:
		self.path = path
		self.skill_name = skill_name


_SKILL_SOURCE_INDEX: dict[int, SkillSourceLocation] = {}
_condition_checkbox_state: dict[tuple[int, str], bool] = {}
_condition_input_state: dict[tuple[int, str], str] = {}


class ConditionSummary:
	__slots__ = ("name", "text")

	def __init__(self, name: str, text: str) -> None:
		self.name = name
		self.text = text


class SkillEditSnapshot:
	__slots__ = (
		"slot",
		"skill_id",
		"name",
		"target",
		"target_value",
		"nature",
		"nature_value",
		"skill_type",
		"skill_type_value",
		"active_conditions",
		"condition_values",
	)

	def __init__(
		self,
		slot: int,
		skill_id: int,
		name: str,
		target: str,
		target_value: Optional[int],
		nature: str,
		nature_value: Optional[int],
		skill_type: str,
		skill_type_value: Optional[int],
		active_conditions: Set[str],
		condition_values: dict[str, Any],
	) -> None:
		self.slot = slot
		self.skill_id = skill_id
		self.name = name
		self.target = target
		self.target_value = target_value
		self.nature = nature
		self.nature_value = nature_value
		self.skill_type = skill_type
		self.skill_type_value = skill_type_value
		self.active_conditions = set(active_conditions)
		self.condition_values = dict(condition_values)


_LOGIC_REPLACEMENTS: tuple[tuple[str, str], ...] = (
	("self.", ""),
	("Player.GetAgentID()", "Self"),
	("Player.GetTargetID()", "current target"),
	("self.heroic_refrain", "Heroic Refrain"),
	("Routines.Agents.", ""),
	("TargetLowestAlly", "Lowest Ally"),
	("TargetLowestAllyCaster", "Lowest Ally Caster"),
	("TargetLowestAllyMartial", "Lowest Ally Martial"),
	("TargetLowestAllyMelee", "Lowest Ally Melee"),
	("TargetLowestAllyRanged", "Lowest Ally Ranged"),
	("TargetLowestAllyEnergy", "Lowest Ally Energy"),
	("TargetClusteredEnemy", "Clustered Enemy"),
	("GetNearestEnemy", "Nearest Enemy"),
	("GetNearestEnemyCaster", "Nearest Enemy Caster"),
	("GetNearestEnemyMartial", "Nearest Enemy Martial"),
	("GetNearestEnemyMelee", "Nearest Enemy Melee"),
	("GetNearestEnemyRanged", "Nearest Enemy Ranged"),
	("GetNearestSpirit", "Nearest Spirit"),
	("GetLowestMinion", "Lowest Minion"),
	("GetNearestCorpse", "Nearest Corpse"),
	("TargetingStrict", "Targeting Strict"),
	("HasEffect", "HasEffect"),
	("Agent.", ""),
)

_RETURN_REPLACEMENTS: dict[str, str] = {
	"Player.GetAgentID()": "Target = Self",
	"Player.GetTargetID()": "Target = current target",
	"get_nearest_enemy()": "Target = nearest enemy",
	"get_lowest_ally()": "Target = lowest ally",
	"self.GetPartyTarget()": "Target = party target",
	"0": "Target = 0",
	"v_target": "Target = computed value",
}


def _humanize_expression(text: str) -> str:
	result = text
	for needle, repl in _LOGIC_REPLACEMENTS:
		result = result.replace(needle, repl)
	result = result.replace("_", " ")
	result = result.replace("  ", " ")
	return result.strip().strip(":")


def _translate_return_action(expr: str) -> str:
	clean_expr = expr.strip()
	if clean_expr in _RETURN_REPLACEMENTS:
		return _RETURN_REPLACEMENTS[clean_expr]
	return f"return {_humanize_expression(clean_expr)}"


def _summarize_logic_block(block_text: str) -> str:
	lines: list[str] = []
	pending_condition = ""
	for raw_line in block_text.splitlines():
		stripped = raw_line.strip()
		if not stripped or stripped.startswith("#"):
			continue
		if stripped.startswith(("if ", "elif ")):
			condition = stripped.split(" ", 1)[1].rstrip(":")
			pending_condition = _humanize_expression(condition)
			continue
		if stripped.startswith("else:"):
			pending_condition = "otherwise"
			continue
		if stripped.startswith("return "):
			action_expr = stripped[len("return "):]
			action = _translate_return_action(action_expr)
			if pending_condition:
				lines.append(f"{action} when {pending_condition}")
				pending_condition = ""
			else:
				lines.append(action)
			continue
		humanized = _humanize_expression(stripped)
		if pending_condition:
			lines.append(f"{humanized} when {pending_condition}")
			pending_condition = ""
		else:
			lines.append(humanized)
	return "\n".join(lines)


def _resolve_project_root() -> Path:
	project_path = Py4GW.Console.get_projects_path()
	if project_path:
		try:
			return Path(project_path).resolve()
		except (OSError, RuntimeError, ValueError):
			pass
	return Path(__file__).resolve().parents[3]


def _texture_full_path(texture_rel: Optional[str]) -> Optional[str]:
	if not texture_rel:
		return None
	texture_path = Path(texture_rel)
	if not texture_path.is_absolute():
		texture_path = _PROJECT_ROOT / texture_rel
	return str(texture_path)


MAX_SKILL_SLOTS = 8
_selected_account_email: Optional[str] = None
_PROJECT_ROOT = _resolve_project_root()
_combat_file_path = _PROJECT_ROOT / "HeroAI" / "combat.py"
_CUSTOM_SKILL_SRC_DIR = _PROJECT_ROOT / "HeroAI" / "custom_skill_src"
_CUSTOM_SKILL_MODULE_PREFIX = "HeroAI.custom_skill_src."
_edit_window_open = False
_edit_snapshot: Optional[SkillEditSnapshot] = None



def _parse_combat_specials() -> tuple[dict[str, str], dict[str, str]]:
	alias_map: dict[str, str] = {}
	cast_logic: dict[str, str] = {}
	target_logic: dict[str, str] = {}

	if not _combat_file_path.exists():
		return cast_logic, target_logic

	try:
		lines = _combat_file_path.read_text(encoding="utf-8").splitlines()
	except OSError:
		return cast_logic, target_logic

	alias_pattern = re.compile(r"self\.(\w+)\s*=\s*GLOBAL_CACHE\.Skill\.GetID\(\"([^\"]+)\"")
	for line in lines:
		match = alias_pattern.search(line)
		if match:
			alias_map[match.group(1)] = match.group(2)

	def assign_logic(alias_names: list[str], block_text: str, store: dict[str, str]) -> None:
		clean_text = block_text.strip()
		if not clean_text:
			return
		pretty_text = _summarize_logic_block(clean_text)
		payload = pretty_text if pretty_text else clean_text
		for alias in alias_names:
			skill_name = alias_map.get(alias)
			if not skill_name:
				continue
			skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
			variants = {
				skill_name,
				skill_name.replace("_", " "),
				skill_name.replace(" ", "_"),
				skill_name.lower(),
				skill_name.replace("_", " ").lower(),
				skill_name.replace(" ", "_").lower(),
			}
			if skill_id:
				variants.add(str(skill_id))
			for key in variants:
				store[key] = payload

	current_func: Optional[str] = None
	idx = 0
	while idx < len(lines):
		line = lines[idx]
		stripped = line.lstrip()
		indent = len(line) - len(stripped)
		if stripped.startswith("def "):
			if stripped.startswith("def AreCastConditionsMet"):
				current_func = "cast"
			elif stripped.startswith("def GetAppropiateTarget"):
				current_func = "target"
			else:
				current_func = None
		if current_func and "self.skills[slot].skill_id" in line and stripped.startswith(("if", "elif")):
			condition_lines = [line]
			scan_idx = idx + 1
			if ":" not in line:
				while scan_idx < len(lines):
					condition_lines.append(lines[scan_idx])
					if ":" in lines[scan_idx]:
						scan_idx += 1
						break
					scan_idx += 1
			else:
				scan_idx = idx + 1
			alias_candidates = re.findall(r"self\.(\w+)", "\n".join(condition_lines))
			alias_names = sorted({alias for alias in alias_candidates if alias in alias_map})
			block_lines: list[str] = []
			block_idx = scan_idx
			while block_idx < len(lines):
				next_line = lines[block_idx]
				if not next_line.strip():
					block_lines.append("")
					block_idx += 1
					continue
				next_indent = len(next_line) - len(next_line.lstrip())
				if next_indent <= indent:
					break
				block_lines.append(next_line)
				block_idx += 1
			block_text = textwrap.dedent("\n".join(block_lines)).strip()
			if block_text and alias_names:
				if current_func == "cast":
					assign_logic(alias_names, block_text, cast_logic)
				else:
					assign_logic(alias_names, block_text, target_logic)
			idx = block_idx
			continue
		idx += 1

	return cast_logic, target_logic


SPECIAL_BEHAVIOR_MAP, SPECIAL_TARGET_MAP = _parse_combat_specials()


def _build_skill_source_index() -> None:
	if not _CUSTOM_SKILL_SRC_DIR.exists():
		return
	pattern = re.compile(r'GLOBAL_CACHE\.Skill\.GetID\("([^\"]+)"\)')
	index: dict[int, SkillSourceLocation] = {}
	for path in _CUSTOM_SKILL_SRC_DIR.rglob("*.py"):
		try:
			text = path.read_text(encoding="utf-8")
		except OSError:
			continue
		for match in pattern.finditer(text):
			skill_name = match.group(1)
			skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
			if not skill_id or skill_id in index:
				continue
			index[skill_id] = SkillSourceLocation(path=path, skill_name=skill_name)
	if index:
		_SKILL_SOURCE_INDEX.clear()
		_SKILL_SOURCE_INDEX.update(index)


_build_skill_source_index()


def _reload_custom_skill_modules() -> None:
	importlib.invalidate_caches()
	module_names: list[str] = []
	for name in tuple(sys.modules.keys()):
		if name.startswith(_CUSTOM_SKILL_MODULE_PREFIX):
			module_names.append(name)
	if "HeroAI.custom_skill" in sys.modules:
		module_names.append("HeroAI.custom_skill")
	# Reload submodules first, then the parent custom_skill module to refresh bindings.
	for module_name in sorted(set(module_names)):
		module = sys.modules.get(module_name)
		if module is None:
			continue
		try:
			importlib.reload(module)
		except Exception as exc:  # noqa: BLE001
			Py4GW.Console.Log(
				MODULE_NAME,
				f"Failed to reload {module_name}: {exc}",
				Py4GW.Console.MessageType.Warning,
			)


def _rebind_custom_skill_classes() -> None:
	"""Refresh imported class bindings after reloading modules."""
	global CustomSkillClass, CastConditions, CustomSkill
	try:
		import HeroAI.custom_skill as custom_skill_module
		custom_skill_module = importlib.reload(custom_skill_module)
		CustomSkillClass = custom_skill_module.CustomSkillClass
	except Exception:
		pass
	try:
		import HeroAI.custom_skill_src.skill_types as skill_types_module
		skill_types_module = importlib.reload(skill_types_module)
		CastConditions = skill_types_module.CastConditions
		CustomSkill = skill_types_module.CustomSkill
	except Exception:
		pass


def _rebuild_default_conditions() -> None:
	"""Recreate default condition values after class reloads."""
	global _default_conditions, DEFAULT_CONDITION_VALUES, _CONDITION_OPTIONS
	_default_conditions = CastConditions()
	DEFAULT_CONDITION_VALUES = {name: deepcopy(value) for name, value in vars(_default_conditions).items()}
	_CONDITION_OPTIONS = tuple(sorted(DEFAULT_CONDITION_VALUES.keys(), key=lambda name: name.lower()))
	_condition_checkbox_state.clear()
	_condition_input_state.clear()


def _refresh_custom_skills() -> None:
	global custom_skill_provider
	_reload_custom_skill_modules()
	_rebind_custom_skill_classes()
	_rebuild_default_conditions()
	custom_skill_provider = CustomSkillClass()
	_build_skill_source_index()


def _reload_heroai_runtime_skills() -> None:
	"""Reload skill modules and push fresh data into runtime handlers."""
	_refresh_custom_skills()
	results: list[str] = []
	try:
		new_handler = CustomSkillClass()
		try:
			import HeroAI.combat as combat_module
			combat_module.custom_skill_data_handler = new_handler
			results.append("Combat")
		except Exception as exc:  # noqa: BLE001
			results.append(f"Combat failed: {exc}")
		try:
			import Py4GWCoreLib.SkillManager as skill_manager_module
			skill_manager_module.SkillManager.Autocombat.custom_skill_data_handler = new_handler
			results.append("SkillManager")
		except Exception as exc:  # noqa: BLE001
			results.append(f"SkillManager failed: {exc}")
	except Exception as exc:  # noqa: BLE001
		results.append(f"Init failed: {exc}")
	if results:
		Py4GW.Console.Log(MODULE_NAME, "; ".join(results), Py4GW.Console.MessageType.Info)


# Ensure the in-memory skills reflect the latest source files when the widget loads.
_refresh_custom_skills()


def _reset_condition_editor_state(skill_id: int) -> None:
	if skill_id <= 0:
		return
	keys_to_remove = [key for key in _condition_checkbox_state if key[0] == skill_id]
	for key in keys_to_remove:
		_condition_checkbox_state.pop(key, None)
	input_keys = [key for key in _condition_input_state if key[0] == skill_id]
	for key in input_keys:
		_condition_input_state.pop(key, None)


def _load_condition_block(skill_id: int) -> tuple[Optional[dict[str, Any]], str]:
	location = _SKILL_SOURCE_INDEX.get(skill_id)
	if location is None:
		_build_skill_source_index()
		location = _SKILL_SOURCE_INDEX.get(skill_id)
		if location is None:
			return None, "Skill source definition could not be located."
	try:
		original_text = location.path.read_text(encoding="utf-8")
	except OSError as exc:
		return None, f"Failed to read file: {exc}"
	marker = f'GLOBAL_CACHE.Skill.GetID("{location.skill_name}")'
	block_start = original_text.find(marker)
	if block_start == -1:
		return None, "Skill section was not found."
	next_block = original_text.find("skill = CustomSkill()", block_start + len(marker))
	block_end = next_block if next_block != -1 else len(original_text)
	block_text = original_text[block_start:block_end]
	newline = "\r\n" if "\r\n" in block_text else "\n"
	return (
		{
			"location": location,
			"original_text": original_text,
			"block_start": block_start,
			"block_end": block_end,
			"block_text": block_text,
			"lines": block_text.splitlines(keepends=True),
			"newline": newline,
		},
		"",
	)


def _write_condition_block(block_data: dict[str, Any]) -> tuple[bool, str]:
	lines = block_data["lines"]
	updated_block = "".join(lines)
	if updated_block == block_data["block_text"]:
		return False, "No changes made."
	updated_text = (
		block_data["original_text"][: block_data["block_start"]]
		+ updated_block
		+ block_data["original_text"][block_data["block_end"] :]
	)
	try:
		block_data["location"].path.write_text(updated_text, encoding="utf-8")
	except OSError as exc:
		return False, f"Failed to write file: {exc}"
	return True, ""


def _detect_block_indent(lines: list[str]) -> str:
	for probe in ("skill.Conditions", "skill.Nature", "skill.TargetAllegiance", "skill.SkillType", "skill.SkillID"):
		for line in lines:
			stripped = line.lstrip("\t ")
			if stripped.startswith(probe):
				return line[: len(line) - len(stripped)] or "\t"
	return "\t"


def _find_insertion_index(lines: list[str]) -> Optional[int]:
	for idx, line in enumerate(lines):
		if line.lstrip().startswith("skill_data["):
			return idx
	return None


def _locate_condition_line(lines: list[str], condition_name: str) -> tuple[Optional[int], Optional[str], Optional[str], str]:
	pattern = re.compile(rf'^([\t ]*)skill\.Conditions\.{re.escape(condition_name)}\s*=\s*(.+?)\s*$')
	for idx, line in enumerate(lines):
		stripped = line.rstrip("\r\n")
		match = pattern.match(stripped)
		if match:
			line_ending = ""
			if line.endswith("\r\n"):
				line_ending = "\r\n"
			elif line.endswith("\n"):
				line_ending = "\n"
			return idx, match.group(1) or "\t", match.group(2).strip(), line_ending or "\n"
	return None, None, None, "\n"


def _remove_condition_line(lines: list[str], index: int) -> None:
	lines.pop(index)
	if index < len(lines) and not lines[index].strip():
		lines.pop(index)


def _input_text(label: str, current_value: str) -> tuple[bool, str]:
	result = PyImGui.input_text(label, current_value, 0)
	if isinstance(result, tuple):
		changed, text_value = result
		return bool(changed), str(text_value)
	text_value = str(result)
	return text_value != current_value, text_value



def _lookup_special_rule(skill_id: int, store: dict[str, str]) -> Optional[str]:
	if not skill_id or not store:
		return None
	skill_name = GLOBAL_CACHE.Skill.GetName(skill_id)
	if not skill_name:
		return None
	candidates = {
		skill_name,
		skill_name.replace(" ", "_"),
		skill_name.replace("_", " "),
		skill_name.lower(),
		skill_name.replace("_", " ").lower(),
	}
	skill_id_str = str(skill_id)
	candidates.add(skill_id_str)
	for key in candidates:
		if key in store:
			return store[key]
	return None


def _persist_skill_target(skill_id: int, target_enum: Skilltarget) -> tuple[bool, str]:
	location = _SKILL_SOURCE_INDEX.get(skill_id)
	if location is None:
		_build_skill_source_index()
		location = _SKILL_SOURCE_INDEX.get(skill_id)
		if location is None:
			return False, "Skill source definition could not be located."
	try:
		original_text = location.path.read_text(encoding="utf-8")
	except OSError as exc:
		return False, f"Failed to read file: {exc}"
	marker = f'GLOBAL_CACHE.Skill.GetID("{location.skill_name}")'
	block_start = original_text.find(marker)
	if block_start == -1:
		return False, "Skill section was not found."
	next_block = original_text.find("skill = CustomSkill()", block_start + len(marker))
	block_end = next_block if next_block != -1 else len(original_text)
	block_text = original_text[block_start:block_end]
	target_line = f"skill.TargetAllegiance = Skilltarget.{target_enum.name}.value"
	target_pattern = re.compile(r'skill\.TargetAllegiance\s*=\s*Skilltarget\.[A-Za-z_]+\.value')
	match = target_pattern.search(block_text)
	if match:
		if block_text[match.start():match.end()] == target_line:
			return False, "Target is already set."
		updated_block = block_text[:match.start()] + target_line + block_text[match.end():]
	else:
		insert_pattern = re.compile(r'skill\.SkillType\s*=\s*SkillType\.[A-Za-z_]+\.value')
		insert_match = insert_pattern.search(block_text)
		if not insert_match:
			return False, "No insertion point for target found."
		insert_pos = insert_match.end()
		indent_match = re.search(r'\n([\t ]+)skill\.SkillID', block_text)
		indent = indent_match.group(1) if indent_match else "\t"
		updated_block = block_text[:insert_pos] + f"\n{indent}{target_line}" + block_text[insert_pos:]
	if updated_block == block_text:
		return False, "No changes made."
	updated_text = original_text[:block_start] + updated_block + original_text[block_end:]
	try:
		location.path.write_text(updated_text, encoding="utf-8")
	except OSError as exc:
		return False, f"Failed to write file: {exc}"
	return True, f"Target updated in {location.path.name}."


def _persist_skill_nature(skill_id: int, nature_enum: SkillNature) -> tuple[bool, str]:
	location = _SKILL_SOURCE_INDEX.get(skill_id)
	if location is None:
		_build_skill_source_index()
		location = _SKILL_SOURCE_INDEX.get(skill_id)
		if location is None:
			return False, "Skill source definition could not be located."
	try:
		original_text = location.path.read_text(encoding="utf-8")
	except OSError as exc:
		return False, f"Failed to read file: {exc}"
	marker = f'GLOBAL_CACHE.Skill.GetID("{location.skill_name}")'
	block_start = original_text.find(marker)
	if block_start == -1:
		return False, "Skill section was not found."
	next_block = original_text.find("skill = CustomSkill()", block_start + len(marker))
	block_end = next_block if next_block != -1 else len(original_text)
	block_text = original_text[block_start:block_end]
	nature_line = f"skill.Nature = SkillNature.{nature_enum.name}.value"
	# Be lenient: match any existing Nature assignment, even if it was previously malformed.
	nature_pattern = re.compile(r'skill\.Nature\s*=\s*.+')
	match = nature_pattern.search(block_text)
	if match:
		if block_text[match.start():match.end()] == nature_line:
			return False, "Nature is already set."
		updated_block = block_text[:match.start()] + nature_line + block_text[match.end():]
	else:
		insert_pattern = re.compile(r'skill\.TargetAllegiance\s*=\s*Skilltarget\.[A-Za-z_]+\.value')
		insert_match = insert_pattern.search(block_text)
		if not insert_match:
			insert_pattern = re.compile(r'skill\.SkillType\s*=\s*SkillType\.[A-Za-z_]+\.value')
			insert_match = insert_pattern.search(block_text)
		if not insert_match:
			return False, "No insertion point for nature found."
		insert_pos = insert_match.end()
		indent_match = re.search(r'\n([\t ]+)skill\.Nature', block_text) or re.search(r'\n([\t ]+)skill\.TargetAllegiance', block_text)
		if not indent_match:
			indent_match = re.search(r'\n([\t ]+)skill\.SkillType', block_text)
		indent = indent_match.group(1) if indent_match else "\t"
		updated_block = block_text[:insert_pos] + f"\n{indent}{nature_line}" + block_text[insert_pos:]
	if updated_block == block_text:
		return False, "No changes made."
	updated_text = original_text[:block_start] + updated_block + original_text[block_end:]
	try:
		location.path.write_text(updated_text, encoding="utf-8")
		# Verify the write actually landed by re-reading the file and checking for the desired line inside the skill block.
		reloaded = location.path.read_text(encoding="utf-8")
		recheck_start = reloaded.find(marker)
		if recheck_start != -1:
			recheck_end = reloaded.find("skill = CustomSkill()", recheck_start + len(marker))
			segment = reloaded[recheck_start : recheck_end if recheck_end != -1 else len(reloaded)]
			if nature_line not in segment:
				return False, f"Verification failed; nature not updated in {location.path.name}."
	except OSError as exc:
		return False, f"Failed to write file: {exc}"
	return True, f"Nature updated in {location.path.name}."


def _persist_skill_type(skill_id: int, type_enum: SkillType) -> tuple[bool, str]:
	location = _SKILL_SOURCE_INDEX.get(skill_id)
	if location is None:
		_build_skill_source_index()
		location = _SKILL_SOURCE_INDEX.get(skill_id)
		if location is None:
			return False, "Skill source definition could not be located."
	try:
		original_text = location.path.read_text(encoding="utf-8")
	except OSError as exc:
		return False, f"Failed to read file: {exc}"
	marker = f'GLOBAL_CACHE.Skill.GetID("{location.skill_name}")'
	block_start = original_text.find(marker)
	if block_start == -1:
		return False, "Skill section was not found."
	next_block = original_text.find("skill = CustomSkill()", block_start + len(marker))
	block_end = next_block if next_block != -1 else len(original_text)
	block_text = original_text[block_start:block_end]
	type_line = f"skill.SkillType = SkillType.{type_enum.name}.value"
	type_pattern = re.compile(r'skill\.SkillType\s*=\s*.+')
	match = type_pattern.search(block_text)
	if match:
		if block_text[match.start():match.end()] == type_line:
			return False, "SkillType is already set."
		updated_block = block_text[:match.start()] + type_line + block_text[match.end():]
	else:
		insert_pattern = re.compile(r'skill\.SkillID\s*=\s*GLOBAL_CACHE\.Skill\.GetID\("[^"]+"\)')
		insert_match = insert_pattern.search(block_text)
		if not insert_match:
			return False, "No insertion point for SkillType found."
		insert_pos = insert_match.end()
		indent_match = re.search(r'\n([\t ]+)skill\.SkillType', block_text)
		if not indent_match:
			indent_match = re.search(r'\n([\t ]+)skill\.SkillID', block_text)
		indent = indent_match.group(1) if indent_match else "\t"
		updated_block = block_text[:insert_pos] + f"\n{indent}{type_line}" + block_text[insert_pos:]
	if updated_block == block_text:
		return False, "No changes made."
	updated_text = original_text[:block_start] + updated_block + original_text[block_end:]
	try:
		location.path.write_text(updated_text, encoding="utf-8")
		reloaded = location.path.read_text(encoding="utf-8")
		recheck_start = reloaded.find(marker)
		if recheck_start != -1:
			recheck_end = reloaded.find("skill = CustomSkill()", recheck_start + len(marker))
			segment = reloaded[recheck_start : recheck_end if recheck_end != -1 else len(reloaded)]
			if type_line not in segment:
				return False, f"Verification failed; SkillType not updated in {location.path.name}."
	except OSError as exc:
		return False, f"Failed to write file: {exc}"
	return True, f"SkillType updated in {location.path.name}."


def _change_skill_target(skill_id: int, new_enum: Skilltarget) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify the target of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_skill_target(skill_id, new_enum)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _change_skill_nature(skill_id: int, new_enum: SkillNature) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify the nature of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_skill_nature(skill_id, new_enum)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _change_skill_type(skill_id: int, new_enum: SkillType) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify the skill type of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_skill_type(skill_id, new_enum)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _persist_condition_flag(skill_id: int, condition_name: str, flag_value: bool) -> tuple[bool, str]:
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if not isinstance(default_value, bool):
		return False, f"{condition_name} is not a toggle condition."
	block_data, error = _load_condition_block(skill_id)
	if block_data is None:
		return False, error
	lines: list[str] = block_data["lines"]
	index, indent, current_literal, line_ending = _locate_condition_line(lines, condition_name)
	default_literal = "True" if default_value else "False"
	desired_literal = "True" if flag_value else "False"
	location_name = block_data["location"].path.name
	if index is not None:
		if flag_value == default_value:
			_remove_condition_line(lines, index)
			message = f"{condition_name} reset to default ({default_literal}) in {location_name}."
		elif current_literal == desired_literal:
			return False, "Condition already set to that value."
		else:
			lines[index] = f"{indent}skill.Conditions.{condition_name} = {desired_literal}{line_ending}"
			message = f"{condition_name} set to {desired_literal} in {location_name}."
	else:
		if flag_value == default_value:
			return False, f"{condition_name} already at default ({default_literal})."
		indent = _detect_block_indent(lines)
		insert_at = _find_insertion_index(lines)
		if insert_at is None:
			return False, "No insertion point for conditions found."
		lines.insert(insert_at, f"{indent}skill.Conditions.{condition_name} = {desired_literal}{block_data['newline']}")
		message = f"{condition_name} set to {desired_literal} in {location_name}."
	success, write_message = _write_condition_block(block_data)
	if not success:
		return False, write_message
	return True, message


def _format_numeric_literal(value: float | int, treat_as_float: bool) -> str:
	if treat_as_float:
		text = f"{float(value):.6f}".rstrip("0").rstrip(".")
		return text or "0"
	return str(int(value))


def _numeric_values_equal(lhs: float | int, rhs: float | int, treat_as_float: bool) -> bool:
	if treat_as_float:
		return abs(float(lhs) - float(rhs)) <= EPSILON
	return int(lhs) == int(rhs)


def _persist_condition_scalar(skill_id: int, condition_name: str, new_value: float | int) -> tuple[bool, str]:
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if isinstance(default_value, bool) or not isinstance(default_value, (int, float)):
		return False, f"{condition_name} is not a numeric condition."
	block_data, error = _load_condition_block(skill_id)
	if block_data is None:
		return False, error
	lines: list[str] = block_data["lines"]
	index, indent, current_literal, line_ending = _locate_condition_line(lines, condition_name)
	is_float = isinstance(default_value, float)
	location_name = block_data["location"].path.name
	default_literal = _format_numeric_literal(default_value, is_float)
	sanitized_value = float(new_value) if is_float else int(new_value)
	desired_literal = _format_numeric_literal(sanitized_value, is_float)
	is_default_target = _numeric_values_equal(sanitized_value, default_value, is_float)
	if index is not None:
		if is_default_target:
			_remove_condition_line(lines, index)
			message = f"{condition_name} reset to default ({default_literal}) in {location_name}."
		elif current_literal == desired_literal:
			return False, "Condition already set to that value."
		else:
			lines[index] = f"{indent}skill.Conditions.{condition_name} = {desired_literal}{line_ending}"
			message = f"{condition_name} set to {desired_literal} in {location_name}."
	else:
		if is_default_target:
			return False, f"{condition_name} already at default ({default_literal})."
		indent = _detect_block_indent(lines)
		insert_at = _find_insertion_index(lines)
		if insert_at is None:
			return False, "No insertion point for conditions found."
		lines.insert(
			insert_at,
			f"{indent}skill.Conditions.{condition_name} = {desired_literal}{block_data['newline']}",
		)
		message = f"{condition_name} set to {desired_literal} in {location_name}."
	success, write_message = _write_condition_block(block_data)
	if not success:
		return False, write_message
	return True, message


def _change_condition_bool(skill_id: int, condition_name: str, new_value: bool) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify conditions of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_condition_flag(skill_id, condition_name, new_value)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _apply_condition_bool_change(skill_id: int, condition_name: str, desired_value: Optional[bool]) -> None:
	if desired_value is None:
		return
	if not _change_condition_bool(skill_id, condition_name, bool(desired_value)):
		return
	key = (skill_id, condition_name)
	_condition_checkbox_state[key] = bool(desired_value)
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
		current_bool = bool(desired_value)
		if isinstance(default_value, bool) and current_bool == default_value:
			_edit_snapshot.active_conditions.discard(condition_name)
		else:
			_edit_snapshot.active_conditions.add(condition_name)
		_edit_snapshot.condition_values[condition_name] = current_bool


def _change_condition_scalar(skill_id: int, condition_name: str, new_value: float | int) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify conditions of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_condition_scalar(skill_id, condition_name, new_value)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _parse_numeric_input(raw_value: Optional[str], treat_as_float: bool) -> Optional[float | int]:
	if raw_value is None:
		return None
	trimmed = raw_value.strip()
	if not trimmed:
		return None
	try:
		parsed = float(trimmed)
	except ValueError:
		return None
	if treat_as_float:
		return parsed
	if not parsed.is_integer():
		return None
	return int(parsed)


def _apply_condition_scalar_change(skill_id: int, condition_name: str, pending_value: Optional[str]) -> None:
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if isinstance(default_value, bool) or not isinstance(default_value, (int, float)):
		return
	treat_as_float = isinstance(default_value, float)
	parsed_value = _parse_numeric_input(pending_value, treat_as_float)
	if parsed_value is None:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Invalid value for {condition_name}.",
			Py4GW.Console.MessageType.Warning,
		)
		return
	if not _change_condition_scalar(skill_id, condition_name, parsed_value):
		return
	key = (skill_id, condition_name)
	_condition_input_state[key] = _format_numeric_literal(parsed_value, treat_as_float)
	if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
		if _numeric_values_equal(parsed_value, default_value, treat_as_float):
			_edit_snapshot.active_conditions.discard(condition_name)
		else:
			_edit_snapshot.active_conditions.add(condition_name)
		_edit_snapshot.condition_values[condition_name] = parsed_value


def _format_list_literal(values: list[int]) -> str:
	if not values:
		return "[]"
	return "[" + ", ".join(str(int(value)) for value in values) + "]"


def _format_list_input(values: list[int]) -> str:
	return ", ".join(str(int(value)) for value in values)


def _lists_equal(lhs: list[int], rhs: list[int]) -> bool:
	return list(lhs) == list(rhs)


def _persist_condition_list(skill_id: int, condition_name: str, new_values: list[int]) -> tuple[bool, str]:
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if not isinstance(default_value, list):
		return False, f"{condition_name} is not a list condition."
	block_data, error = _load_condition_block(skill_id)
	if block_data is None:
		return False, error
	lines: list[str] = block_data["lines"]
	index, indent, current_literal, line_ending = _locate_condition_line(lines, condition_name)
	location_name = block_data["location"].path.name
	sanitized_values = [int(value) for value in new_values]
	default_literal = _format_list_literal(default_value)
	desired_literal = _format_list_literal(sanitized_values)
	is_default_target = _lists_equal(sanitized_values, default_value)
	if index is not None:
		if is_default_target:
			_remove_condition_line(lines, index)
			message = f"{condition_name} reset to default ({default_literal}) in {location_name}."
		elif current_literal == desired_literal:
			return False, "Condition already set to that value."
		else:
			lines[index] = f"{indent}skill.Conditions.{condition_name} = {desired_literal}{line_ending}"
			message = f"{condition_name} set to {desired_literal} in {location_name}."
	else:
		if is_default_target:
			return False, f"{condition_name} already at default ({default_literal})."
		indent = _detect_block_indent(lines)
		insert_at = _find_insertion_index(lines)
		if insert_at is None:
			return False, "No insertion point for conditions found."
		lines.insert(
			insert_at,
			f"{indent}skill.Conditions.{condition_name} = {desired_literal}{block_data['newline']}",
		)
		message = f"{condition_name} set to {desired_literal} in {location_name}."
	success, write_message = _write_condition_block(block_data)
	if not success:
		return False, write_message
	return True, message


def _change_condition_list(skill_id: int, condition_name: str, new_values: list[int]) -> bool:
	if skill_id <= 0:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Cannot modify conditions of an empty skill slot.",
			Py4GW.Console.MessageType.Warning,
		)
		return False
	success, message = _persist_condition_list(skill_id, condition_name, new_values)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if success:
		_refresh_custom_skills()
	return success


def _parse_list_input(raw_value: Optional[str]) -> Optional[list[int]]:
	if raw_value is None:
		return None
	trimmed = raw_value.strip()
	if not trimmed:
		return []
	parts = [part.strip() for part in trimmed.split(",")]
	values: list[int] = []
	for part in parts:
		if not part:
			continue
		try:
			values.append(int(part, 10))
		except ValueError:
			return None
	return values


def _apply_condition_list_change(skill_id: int, condition_name: str, pending_value: Optional[str]) -> None:
	default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
	if not isinstance(default_value, list):
		return
	parsed_values = _parse_list_input(pending_value)
	if parsed_values is None:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Invalid list for {condition_name}. Use comma-separated numeric IDs.",
			Py4GW.Console.MessageType.Warning,
		)
		return
	if not _change_condition_list(skill_id, condition_name, parsed_values):
		return
	key = (skill_id, condition_name)
	_condition_input_state[key] = _format_list_input(parsed_values)
	if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
		if _lists_equal(parsed_values, default_value):
			_edit_snapshot.active_conditions.discard(condition_name)
		else:
			_edit_snapshot.active_conditions.add(condition_name)
		_edit_snapshot.condition_values[condition_name] = list(parsed_values)

def _handle_target_change(row: SkillRow, new_enum: Skilltarget) -> None:
	if not _change_skill_target(row.skill_id, new_enum):
		return
	row.target_value = new_enum.value
	row.target = new_enum.name.replace("_", " ")


class AccountEntry:
	__slots__ = ("label", "email", "character", "account")

	def __init__(self, label: str, email: str, character: str, account: Any) -> None:
		self.label = label
		self.email = email
		self.character = character
		self.account = account


class SkillRow:
	__slots__ = (
		"slot",
		"skill_id",
		"name",
		"texture_path",
		"conditions",
		"target",
		"target_value",
		"nature",
		"nature_value",
		"skill_type",
		"skill_type_value",
		"active_conditions",
		"condition_values",
		"special",
		"special_target",
	)

	def __init__(
		self,
		slot: int,
		skill_id: int,
		name: str,
		texture_path: Optional[str],
		conditions: List[str],
		target: str,
		target_value: Optional[int],
		nature: str,
		nature_value: Optional[int],
		skill_type: str,
		skill_type_value: Optional[int],
		active_conditions: Set[str],
		condition_values: dict[str, Any],
		special: Optional[str],
		special_target: Optional[str],
	) -> None:
		self.slot = slot
		self.skill_id = skill_id
		self.name = name
		self.texture_path = texture_path
		self.conditions = conditions
		self.target = target
		self.target_value = target_value
		self.nature = nature
		self.nature_value = nature_value
		self.skill_type = skill_type
		self.skill_type_value = skill_type_value
		self.active_conditions = active_conditions
		self.condition_values = condition_values
		self.special = special
		self.special_target = special_target


def _build_skill_row(slot: int, skill_id: int) -> SkillRow:
	if not skill_id:
		return SkillRow(slot, 0, "Empty Slot", None, [], "--", None, "--", None, "--", None, set(), {}, None, None)

	skill_name = GLOBAL_CACHE.Skill.GetName(skill_id) or f"Skill {skill_id}"
	skill_name = skill_name.replace("_", " ")
	custom_skill = _safe_get_custom_skill(skill_id)
	conditions, active_conditions, condition_values = _describe_conditions(custom_skill)
	target = _format_target(custom_skill)
	nature = _format_nature(custom_skill)
	skill_type = _format_skill_type(custom_skill)
	special = _get_special_behavior(skill_id)
	special_target = _get_special_target_info(skill_id)
	texture_rel = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
	texture_path = _texture_full_path(texture_rel)
	target_value = custom_skill.TargetAllegiance if custom_skill else None
	nature_value = custom_skill.Nature if custom_skill else None
	skill_type_value = custom_skill.SkillType if custom_skill else None
	return SkillRow(
		slot,
		skill_id,
		skill_name,
		texture_path,
		conditions,
		target,
		target_value,
		nature,
		nature_value,
		skill_type,
		skill_type_value,
		active_conditions,
		condition_values,
		special,
		special_target,
	)


def _prettify_name(name: str) -> str:
	spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("_", " ")
	return spaced.strip()


def _coerce_range_value(value: Any) -> Optional[float]:
	if isinstance(value, Range):
		return float(value.value)
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def _format_range_label(value: Any) -> Optional[str]:
	coerced = _coerce_range_value(value)
	if coerced is None:
		return None
	try:
		return Range(coerced).name.replace("_", " ").title()
	except Exception:
		return None


def _condition_changed(name: str, value: Any) -> bool:
	default_value = DEFAULT_CONDITION_VALUES.get(name)
	if isinstance(value, bool):
		return value != default_value
	if isinstance(value, list):
		return len(value) > 0
	if isinstance(value, (int, float, Range)) or isinstance(default_value, (int, float, Range)):
		lhs = _coerce_range_value(value)
		rhs = _coerce_range_value(default_value)
		if lhs is not None and rhs is not None:
			return abs(lhs - rhs) > EPSILON
	return value != default_value


def _format_condition_value(name: str, value) -> str:
	pretty_name = _prettify_name(name)

	if name in AREA_FIELDS:
		range_label = _format_range_label(value)
		if range_label:
			return f"{pretty_name}: {range_label}"

	if isinstance(value, bool):
		return f"{pretty_name}: {value}"

	if isinstance(value, float):
		if name in PERCENT_FIELDS:
			comparator = "<=" if name.startswith("Less") else ">="
			percent_value = int(value * 100)
			return f"{pretty_name} {comparator} {percent_value}%"
		return f"{pretty_name}: {round(value, 3)}"

	if isinstance(value, int):
		if name in AREA_FIELDS:
			try:
				area_name = Range(value).name.replace("_", " ").title()
			except ValueError:
				area_name = str(value)
			return f"{pretty_name}: {area_name}"
		if name in COUNTER_FIELDS:
			return f"{pretty_name} >= {value}"
		return f"{pretty_name}: {value}"

	if isinstance(value, list):
		if not value:
			return ""
		if name in LIST_FIELDS:
			preview = ", ".join(str(item) for item in value[:3])
			if len(value) > 3:
				preview += f" ... (+{len(value) - 3})"
			return f"{pretty_name}: {preview}"
		return f"{pretty_name}: {len(value)} entries"

	return f"{pretty_name}: {value}"


def _format_condition_raw_value(value: Any) -> str:
	if isinstance(value, bool):
		return "True" if value else "False"
	if isinstance(value, float):
		return f"{value:.3f}".rstrip("0").rstrip(".") or "0"
	if isinstance(value, (int, str)):
		return str(value)
	if isinstance(value, list):
		return f"{len(value)} entries"
	return str(value)


def _resolve_attr(obj: Any, *names: str) -> Optional[Any]:
	"""Return the first matching attribute value for the provided names."""
	for name in names:
		if hasattr(obj, name):
			return getattr(obj, name)
	return None


def _skill_struct_id(struct: Any) -> int:
	if struct is None:
		return 0
	for attr in ("Id", "id", "SkillID", "skill_id"):
		if hasattr(struct, attr):
			value = getattr(struct, attr)
			if hasattr(value, "value"):
				value = value.value
			try:
				return int(value)
			except (TypeError, ValueError):
				continue
	return 0


def _get_skill_struct(container: Any, idx: int) -> Any:
	slot_key = idx + 1
	if container is None:
		return None
	if isinstance(container, dict):
		for key in (slot_key, idx, str(slot_key), str(idx)):
			if key in container:
				return container[key]
		return None
	try:
		return container[idx]
	except (IndexError, KeyError, TypeError, AttributeError):
		return None


def _describe_conditions(skill: Optional["_CustomSkill"]) -> Tuple[List[str], Set[str], dict[str, Any]]:
	if skill is None or not skill.SkillID:
		return [], set(), {}

	summary: List[str] = []
	active_names: Set[str] = set()
	condition_values: dict[str, Any] = {}
	for name, value in vars(skill.Conditions).items():
		if name not in DEFAULT_CONDITION_VALUES:
			continue
		condition_values[name] = value
		if not _condition_changed(name, value):
			continue
		formatted = _format_condition_value(name, value)
		if formatted:
			summary.append(formatted)
			active_names.add(name)
	return summary, active_names, condition_values


def _safe_get_custom_skill(skill_id: int) -> Optional["_CustomSkill"]:
	if skill_id <= 0 or skill_id >= custom_skill_provider.MaxSkillData:
		return None
	try:
		custom_skill = custom_skill_provider.get_skill(skill_id)
	except ValueError:
		return None
	return custom_skill if custom_skill.SkillID else None


def _collect_accounts() -> List[AccountEntry]:
	shmem_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
	entries: List[AccountEntry] = []
	seen: set[str] = set()
	for account in shmem_accounts:
		email = (getattr(account, "AccountEmail", "") or "").strip()
		if not email or email in seen:
			continue
		seen.add(email)
		char_name = (getattr(account, "CharacterName", "") or getattr(account, "AccountName", "") or "").strip()
		entries.append(AccountEntry(label=email, email=email, character=char_name or email or "Unknown", account=account))

	entries.sort(key=lambda entry: entry.label.lower())
	return entries


def _resolve_selected_account(accounts: List[AccountEntry]) -> tuple[Optional[AccountEntry], int]:
	global _selected_account_email
	if not accounts:
		_selected_account_email = None
		return None, -1

	preferred_email = _selected_account_email or (Player.GetAccountEmail() or "")
	idx = next((i for i, entry in enumerate(accounts) if entry.email == preferred_email), -1) if preferred_email else -1
	if idx == -1:
		idx = 0

	_selected_account_email = accounts[idx].email
	return accounts[idx], idx


def _get_special_behavior(skill_id: int) -> Optional[str]:
	return _lookup_special_rule(skill_id, SPECIAL_BEHAVIOR_MAP)


def _get_special_target_info(skill_id: int) -> Optional[str]:
	return _lookup_special_rule(skill_id, SPECIAL_TARGET_MAP)



def _resolve_skillbar_source(account: Any) -> Optional[Any]:
	for owner in (
		account,
		_resolve_attr(account, "PlayerData", "player_data"),
	):
		if owner is None:
			continue
		skillbar_data = _resolve_attr(owner, "SkillbarData", "skillbar_data")
		if skillbar_data is not None:
			return skillbar_data
		agent_data = _resolve_attr(owner, "AgentData", "agent_data")
		if agent_data is None:
			continue
		skillbar_struct = _resolve_attr(agent_data, "Skillbar", "skillbar")
		if skillbar_struct is not None:
			return skillbar_struct
	return None


def _collect_skillbar_entries(account) -> List[SkillRow]:
	if account is None:
		return []

	skillbar_source = _resolve_skillbar_source(account)
	if skillbar_source is None:
		return []

	skill_container = _resolve_attr(skillbar_source, "Skills", "skills")
	if callable(skill_container):
		try:
			skill_container = skill_container()
		except TypeError:
			pass
	if skill_container is None and hasattr(skillbar_source, "__getitem__"):
		skill_container = skillbar_source
	if skill_container is None:
		return []

	entries: List[SkillRow] = []
	for idx in range(MAX_SKILL_SLOTS):
		skill_struct = _get_skill_struct(skill_container, idx)
		skill_id = _skill_struct_id(skill_struct)
		entries.append(_build_skill_row(idx + 1, skill_id))

	local_fallback = _collect_local_skillbar_entries_if_needed(account, entries)
	return local_fallback if local_fallback is not None else entries


def _collect_local_skillbar_entries_if_needed(account, shared_entries: List[SkillRow]) -> Optional[List[SkillRow]]:
	if any(row.skill_id for row in shared_entries):
		return None
	account_email = (getattr(account, "AccountEmail", "") or "").strip().lower()
	local_email = (Player.GetAccountEmail() or "").strip().lower()
	if not account_email or account_email != local_email:
		return None
	rows: List[SkillRow] = []
	for slot in range(1, MAX_SKILL_SLOTS + 1):
		skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
		rows.append(_build_skill_row(slot, skill_id))
	return rows


def _format_target(skill: Optional["_CustomSkill"]) -> str:
	if skill is None:
		return "Unknown"
	try:
		enum_value = Skilltarget(skill.TargetAllegiance)
		return enum_value.name.replace("_", " ")
	except ValueError:
		return str(skill.TargetAllegiance)


def _format_nature(skill: Optional["_CustomSkill"]) -> str:
	if skill is None:
		return "Unknown"
	try:
		enum_value = SkillNature(skill.Nature)
		return enum_value.name.replace("_", " ")
	except ValueError:
		return str(skill.Nature)


def _format_skill_type(skill: Optional["_CustomSkill"]) -> str:
	if skill is None:
		return "Unknown"
	try:
		enum_value = SkillType(skill.SkillType)
		return enum_value.name.replace("_", " ")
	except ValueError:
		return str(skill.SkillType)


def _summarize_snapshot_conditions(active_conditions: Set[str], condition_values: dict[str, Any]) -> List[str]:
	lines: List[str] = []
	for name in sorted(active_conditions, key=str.lower):
		value = condition_values.get(name, DEFAULT_CONDITION_VALUES.get(name))
		formatted = _format_condition_value(name, value)
		if formatted:
			lines.append(formatted)
	return lines


def _describe_nature(value: Optional[int], fallback_label: str) -> str:
	if value is not None:
		try:
			enum_value = SkillNature(value)
			return _NATURE_DESCRIPTIONS.get(enum_value, "Custom nature bucket for bespoke logic.")
		except ValueError:
			pass
	label = (fallback_label or "").strip().lower()
	for enum_value in _NATURE_OPTIONS:
		if enum_value.name.replace("_", " ").lower() == label:
			return _NATURE_DESCRIPTIONS.get(enum_value, "Custom nature bucket for bespoke logic.")
	return "Nature guides targeting/usage heuristics for the skill."


def _build_nature_tooltip(selected_value: Optional[int], fallback_label: str) -> str:
	current_match: Optional[SkillNature] = None
	if selected_value is not None:
		try:
			current_match = SkillNature(selected_value)
		except ValueError:
			current_match = None
	elif fallback_label:
		lower = fallback_label.strip().lower()
		for enum_value in _NATURE_OPTIONS:
			if enum_value.name.replace("_", " ").lower() == lower:
				current_match = enum_value
				break
	lines: list[str] = []
	for option in _NATURE_OPTIONS:
		label = option.name.replace("_", " ")
		desc = _NATURE_DESCRIPTIONS.get(option, "Custom nature bucket for bespoke logic.")
		marker = "(current) " if option == current_match else ""
		lines.append(f"{marker}{label}: {desc}")
	return "\n".join(lines)


def _build_skilltype_tooltip(selected_value: Optional[int], fallback_label: str) -> str:
	current_match: Optional[SkillType] = None
	if selected_value is not None:
		try:
			current_match = SkillType(selected_value)
		except ValueError:
			current_match = None
	elif fallback_label:
		lower = fallback_label.strip().lower()
		for enum_value in _SKILLTYPE_OPTIONS:
			if enum_value.name.replace("_", " ").lower() == lower:
				current_match = enum_value
				break
	lines: list[str] = []
	for option in _SKILLTYPE_OPTIONS:
		label = option.name.replace("_", " ")
		desc = _SKILLTYPE_DESCRIPTIONS.get(option, "General skill bucket.")
		marker = "(current) " if option == current_match else ""
		lines.append(f"{marker}{label}: {desc}")
	return "\n".join(lines)


def _build_range_tooltip(current_value: Any) -> str:
	current_match: Optional[Range] = None
	try:
		current_match = Range(current_value)
	except Exception:
		current_match = None
	lines: list[str] = []
	for option in Range:
		label = option.name
		desc = _RANGE_DESCRIPTIONS.get(option, "Range bucket")
		marker = "(current) " if option == current_match else ""
		lines.append(f"{marker}{label}: {desc}")
	return "\n".join(lines)


def _draw_skill_cell(row: SkillRow) -> None:
	if row.texture_path:
		PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
		PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
		PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
		ImGui.ImageButton(f"##heroai_skill_{row.slot}", row.texture_path, ICON_SIZE, ICON_SIZE)
		PyImGui.pop_style_color(3)
		PyImGui.same_line(0, 8)

	PyImGui.begin_group()
	PyImGui.text(row.name)
	if row.skill_id:
		PyImGui.text(f"ID {row.skill_id}")
	else:
		PyImGui.text("No Skill")
	PyImGui.end_group()


def _draw_target_cell(row: SkillRow) -> None:
	display_target = row.target
	display_nature = row.nature
	display_type = row.skill_type
	if _edit_snapshot and _edit_snapshot.skill_id == row.skill_id:
		display_target = _edit_snapshot.target or row.target
		display_nature = _edit_snapshot.nature or row.nature
		display_type = _edit_snapshot.skill_type or row.skill_type
	PyImGui.text(display_target)
	PyImGui.text(f"Nature: {display_nature}")
	PyImGui.text(f"Type: {display_type}")
	if row.special_target:
		PyImGui.spacing()
		PyImGui.text("Special:")
		for line in row.special_target.splitlines():
			clean = line.strip()
			if clean:
				PyImGui.bullet_text(clean)

def _draw_action_cell(row: SkillRow) -> None:
	if row.skill_id == 0:
		PyImGui.text_disabled("--")
		return
	if PyImGui.button(f"View##{row.slot}_{row.skill_id}"):
		_open_edit_window(row)


def _open_edit_window(row: SkillRow) -> None:
	global _edit_window_open, _edit_snapshot
	_reset_condition_editor_state(row.skill_id)
	_edit_snapshot = SkillEditSnapshot(
		row.slot,
		row.skill_id,
		row.name,
		row.target,
		row.target_value,
		row.nature,
		row.nature_value,
		row.skill_type,
		row.skill_type_value,
		row.active_conditions,
		row.condition_values,
	)
	_edit_window_open = True


def _render_target_list(skill_id: int, selected_value: Optional[int], fallback_label: str) -> None:
	current_label = "Unknown"
	if selected_value is not None:
		try:
			current_label = Skilltarget(selected_value).name.replace("_", " ")
		except ValueError:
			current_label = str(selected_value)
	elif fallback_label:
		current_label = fallback_label.title()

	PyImGui.text("Current Target:")
	PyImGui.same_line(0, 6)
	PyImGui.text(current_label)

	if PyImGui.begin_combo("##target_combo", current_label, 0):
		for option in _TARGET_OPTIONS:
			label = option.name.replace("_", " ")
			is_active = selected_value == option.value
			if selected_value is None and label.lower() == (fallback_label or "").lower():
				is_active = True
			if PyImGui.selectable(f"{label}##target_option_{option.value}", is_active, PyImGui.SelectableFlags(0), (0.0, 0.0)):
				if _change_skill_target(skill_id, option):
					if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
						_edit_snapshot.target_value = option.value
						_edit_snapshot.target = label
					selected_value = option.value
					current_label = label
		PyImGui.end_combo()


def _render_nature_list(skill_id: int, selected_value: Optional[int], fallback_label: str) -> None:
	current_label = "Unknown"
	if selected_value is not None:
		try:
			current_label = SkillNature(selected_value).name.replace("_", " ")
		except ValueError:
			current_label = str(selected_value)
	elif fallback_label:
		current_label = fallback_label.title()

	PyImGui.text("Current Nature:")
	PyImGui.same_line(0, 6)
	PyImGui.text(current_label)
	if PyImGui.is_item_hovered():
		PyImGui.begin_tooltip()
		PyImGui.push_text_wrap_pos(520)
		PyImGui.text_wrapped(_build_nature_tooltip(selected_value, fallback_label))
		PyImGui.pop_text_wrap_pos()
		PyImGui.end_tooltip()

	if PyImGui.begin_combo("##nature_combo", current_label, 0):
		for option in _NATURE_OPTIONS:
			label = option.name.replace("_", " ")
			is_active = selected_value == option.value
			if selected_value is None and label.lower() == (fallback_label or "").lower():
				is_active = True
			if PyImGui.selectable(f"{label}##nature_option_{option.value}", is_active, PyImGui.SelectableFlags(0), (0.0, 0.0)):
				if _change_skill_nature(skill_id, option):
					if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
						_edit_snapshot.nature_value = option.value
						_edit_snapshot.nature = label
					selected_value = option.value
					current_label = label
		PyImGui.end_combo()


def _render_skilltype_list(skill_id: int, selected_value: Optional[int], fallback_label: str) -> None:
	current_label = "Unknown"
	if selected_value is not None:
		try:
			current_label = SkillType(selected_value).name.replace("_", " ")
		except ValueError:
			current_label = str(selected_value)
	elif fallback_label:
		current_label = fallback_label.title()

	PyImGui.text("Current SkillType:")
	PyImGui.same_line(0, 6)
	PyImGui.text(current_label)
	if PyImGui.is_item_hovered():
		PyImGui.begin_tooltip()
		PyImGui.push_text_wrap_pos(520)
		PyImGui.text_wrapped(_build_skilltype_tooltip(selected_value, fallback_label))
		PyImGui.pop_text_wrap_pos()
		PyImGui.end_tooltip()

	if PyImGui.begin_combo("##skilltype_combo", current_label, 0):
		for option in _SKILLTYPE_OPTIONS:
			label = option.name.replace("_", " ")
			is_active = selected_value == option.value
			if selected_value is None and label.lower() == (fallback_label or "").lower():
				is_active = True
			if PyImGui.selectable(f"{label}##skilltype_option_{option.value}", is_active, PyImGui.SelectableFlags(0), (0.0, 0.0)):
				if _change_skill_type(skill_id, option):
					if _edit_snapshot and _edit_snapshot.skill_id == skill_id:
						_edit_snapshot.skill_type_value = option.value
						_edit_snapshot.skill_type = label
					selected_value = option.value
					current_label = label
		PyImGui.end_combo()



def _render_condition_list(skill_id: int, active_conditions: Set[str], condition_values: dict[str, Any]) -> None:
	inner_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if not PyImGui.begin_table("##condition_inner_table", 4, inner_flags, 0, 0):
		PyImGui.text_disabled("Conditions could not be loaded.")
		return
	PyImGui.table_setup_column("Condition", PyImGui.TableColumnFlags.WidthFixed, CONDITION_LIST_NAME_WIDTH)
	PyImGui.table_setup_column("Active Value", PyImGui.TableColumnFlags.WidthFixed, CONDITION_LIST_VALUE_WIDTH)
	PyImGui.table_setup_column("", PyImGui.TableColumnFlags.WidthFixed, CONDITION_LIST_CONTROL_WIDTH)
	PyImGui.table_setup_column("", PyImGui.TableColumnFlags.WidthFixed, CONDITION_LIST_APPLY_WIDTH)
	PyImGui.table_headers_row()
	for condition_name in _CONDITION_OPTIONS:
		default_value = DEFAULT_CONDITION_VALUES.get(condition_name)
		PyImGui.table_next_row()
		pretty = _prettify_name(condition_name)
		current_value = condition_values.get(condition_name, default_value)
		is_condition_active = _condition_changed(condition_name, current_value)
		PyImGui.table_set_column_index(0)
		PyImGui.selectable(
			f"{pretty}##condition_option_{condition_name}",
			is_condition_active,
			PyImGui.SelectableFlags(0),
			(0.0, 0.0),
		)
		effective_value = current_value if is_condition_active else default_value
		PyImGui.table_set_column_index(1)
		if is_condition_active:
			PyImGui.text_colored(_format_condition_raw_value(effective_value), _ACTIVE_STATE_COLOR)
		else:
			PyImGui.text_disabled(_format_condition_raw_value(effective_value))
		if condition_name in AREA_FIELDS:
			if PyImGui.is_item_hovered():
				PyImGui.begin_tooltip()
				PyImGui.push_text_wrap_pos(520)
				PyImGui.text_wrapped(_build_range_tooltip(effective_value))
				PyImGui.pop_text_wrap_pos()
				PyImGui.end_tooltip()

		bool_key: Optional[tuple[int, str]] = None
		numeric_key: Optional[tuple[int, str]] = None
		list_key: Optional[tuple[int, str]] = None
		PyImGui.table_set_column_index(2)
		if isinstance(default_value, bool):
			bool_key = (skill_id, condition_name)
			active_bool = current_value if isinstance(current_value, bool) else default_value
			if isinstance(active_bool, bool):
				current_bool = _condition_checkbox_state.get(bool_key)
				if current_bool is None:
					current_bool = active_bool
					_condition_checkbox_state[bool_key] = current_bool
				new_bool = PyImGui.checkbox(
					f"##condition_bool_{condition_name}_{skill_id}",
					current_bool,
				)
				if new_bool != current_bool:
					_condition_checkbox_state[bool_key] = new_bool
			else:
				PyImGui.text_disabled("--")
		elif isinstance(default_value, (int, float)):
			numeric_key = (skill_id, condition_name)
			active_numeric = current_value if current_value is not None else default_value
			if active_numeric is None:
				active_numeric = 0.0 if isinstance(default_value, float) else 0
			current_text = _condition_input_state.get(numeric_key)
			if current_text is None:
				current_text = _format_numeric_literal(active_numeric, isinstance(default_value, float))
				_condition_input_state[numeric_key] = current_text
			control_width = max(CONDITION_LIST_CONTROL_WIDTH - 10, 60)
			PyImGui.push_item_width(control_width)
			changed, new_text = _input_text(
				f"##condition_value_{condition_name}_{skill_id}",
				current_text,
			)
			PyImGui.pop_item_width()
			if changed:
				_condition_input_state[numeric_key] = new_text
		elif isinstance(default_value, list):
			list_key = (skill_id, condition_name)
			active_list = current_value if current_value is not None else default_value
			if active_list is None:
				active_list = []
			current_text = _condition_input_state.get(list_key)
			if current_text is None:
				current_text = _format_list_input(active_list)
				_condition_input_state[list_key] = current_text
			control_width = max(CONDITION_LIST_CONTROL_WIDTH - 10, 60)
			PyImGui.push_item_width(control_width)
			changed, new_text = _input_text(
				f"##condition_list_{condition_name}_{skill_id}",
				current_text,
			)
			PyImGui.pop_item_width()
			if changed:
				_condition_input_state[list_key] = new_text
		else:
			PyImGui.text_disabled("--")

		PyImGui.table_set_column_index(3)
		if bool_key is not None:
			desired_value = _condition_checkbox_state.get(bool_key)
			if desired_value is None and isinstance(default_value, bool):
				desired_value = default_value
			if desired_value is None:
				PyImGui.text_disabled("--")
			elif PyImGui.button(f"Apply##condition_apply_{condition_name}_{skill_id}"):
				_apply_condition_bool_change(skill_id, condition_name, desired_value)
		elif numeric_key is not None:
			pending_value = _condition_input_state.get(numeric_key)
			if PyImGui.button(f"Apply##condition_apply_{condition_name}_{skill_id}"):
				_apply_condition_scalar_change(skill_id, condition_name, pending_value)
		elif list_key is not None:
			pending_list = _condition_input_state.get(list_key)
			apply_clicked = PyImGui.button(f"Apply##condition_apply_{condition_name}_{skill_id}")
			PyImGui.same_line(0, 6)
			delete_clicked = PyImGui.button(f"Delete##condition_delete_{condition_name}_{skill_id}")
			if apply_clicked:
				_apply_condition_list_change(skill_id, condition_name, pending_list)
			elif delete_clicked:
				_condition_input_state[list_key] = ""
				_apply_condition_list_change(skill_id, condition_name, "")
		else:
			PyImGui.text_disabled("--")
	PyImGui.end_table()


def _draw_edit_window() -> None:
	global _edit_window_open, _edit_snapshot
	if not _edit_window_open or _edit_snapshot is None:
		return
	window_flags = PyImGui.WindowFlags.AlwaysAutoResize | PyImGui.WindowFlags.NoCollapse
	opened = PyImGui.begin("Skill Editor", window_flags)
	if not opened:
		PyImGui.end()
		if _edit_snapshot:
			_reset_condition_editor_state(_edit_snapshot.skill_id)
		_edit_window_open = False
		_edit_snapshot = None
		return
	reload_label = "HeroAi reload"
	reload_width = PyImGui.calc_text_size(reload_label)[0] + 12.0
	button_label = "Close Window"
	button_width = PyImGui.calc_text_size(button_label)[0] + 12.0
	try:
		avail_x = PyImGui.get_content_region_avail()[0]
		current_x = PyImGui.get_cursor_pos_x()
		total_width = reload_width + 8.0 + button_width
		PyImGui.set_cursor_pos_x(current_x + max(0.0, avail_x - total_width))
	except Exception:
		total_width = reload_width + 8.0 + button_width
	if PyImGui.button(reload_label):
		_reload_heroai_runtime_skills()
	PyImGui.same_line(0, 8)
	if PyImGui.button(button_label):
		if _edit_snapshot:
			_reset_condition_editor_state(_edit_snapshot.skill_id)
		_edit_window_open = False
		_edit_snapshot = None
		PyImGui.end()
		return
	PyImGui.text(f"Slot {_edit_snapshot.slot}")
	PyImGui.text(f"Skill: {_edit_snapshot.name} (ID {_edit_snapshot.skill_id})")
	PyImGui.text(f"Current Target: {_edit_snapshot.target}")
	PyImGui.text(f"Current Nature: {_edit_snapshot.nature}")
	PyImGui.text(f"Current SkillType: {_edit_snapshot.skill_type}")
	PyImGui.spacing()
	flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if PyImGui.begin_table("##edit_target_options", 2, flags, 0, 0):
		PyImGui.table_setup_column("Target / Nature / Type", PyImGui.TableColumnFlags.WidthFixed, EDIT_POPUP_TARGET_COLUMN_WIDTH)
		PyImGui.table_setup_column("Conditions", PyImGui.TableColumnFlags.WidthFixed, EDIT_POPUP_CONDITION_COLUMN_WIDTH)
		PyImGui.table_headers_row()
		PyImGui.table_next_row()
		PyImGui.table_set_column_index(0)
		_render_target_list(
			_edit_snapshot.skill_id,
			_edit_snapshot.target_value,
			(_edit_snapshot.target or "").lower(),
		)
		PyImGui.spacing()
		_render_nature_list(
			_edit_snapshot.skill_id,
			_edit_snapshot.nature_value,
			(_edit_snapshot.nature or "").lower(),
		)
		PyImGui.spacing()
		_render_skilltype_list(
			_edit_snapshot.skill_id,
			_edit_snapshot.skill_type_value,
			(_edit_snapshot.skill_type or "").lower(),
		)
		PyImGui.table_set_column_index(1)
		_render_condition_list(_edit_snapshot.skill_id, _edit_snapshot.active_conditions, _edit_snapshot.condition_values)
		PyImGui.end_table()
	else:
		PyImGui.text_disabled("Targets could not be loaded.")
	PyImGui.end()


def _draw_condition_cell(row: SkillRow) -> None:
	conditions_to_show = row.conditions
	if _edit_snapshot and _edit_snapshot.skill_id == row.skill_id:
		conditions_to_show = _summarize_snapshot_conditions(_edit_snapshot.active_conditions, _edit_snapshot.condition_values)

	if conditions_to_show:
		for condition in conditions_to_show:
			PyImGui.bullet_text(condition)
	else:
		PyImGui.text("No Conditions")

	if row.special:
		if conditions_to_show:
			PyImGui.spacing()
		PyImGui.text("Special Conditions:")
		for line in row.special.splitlines():
			clean = line.strip()
			if clean:
				PyImGui.bullet_text(clean)


def _draw_skill_table(entries: List[SkillRow]) -> None:
	flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if PyImGui.begin_table("##HeroAiSkillTable", 5, flags, 0, 0):
		PyImGui.table_setup_column("Slot", PyImGui.TableColumnFlags.WidthFixed, 24)
		PyImGui.table_setup_column("Skill", PyImGui.TableColumnFlags.WidthFixed, 320)
		PyImGui.table_setup_column("Target / Nature / Type", PyImGui.TableColumnFlags.WidthFixed, 260)
		PyImGui.table_setup_column("Conditions", PyImGui.TableColumnFlags.WidthStretch, 0)
		PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.WidthFixed, 100)
		PyImGui.table_headers_row()

		for row in entries:
			PyImGui.table_next_row()
			PyImGui.table_set_column_index(0)
			PyImGui.text(f"{row.slot}")

			PyImGui.table_set_column_index(1)
			_draw_skill_cell(row)

			PyImGui.table_set_column_index(2)
			_draw_target_cell(row)

			PyImGui.table_set_column_index(3)
			_draw_condition_cell(row)

			PyImGui.table_set_column_index(4)
			_draw_action_cell(row)

		PyImGui.end_table()


def _draw_window() -> None:
	global _selected_account_email
	if not window_module.begin():
		window_module.end()
		return

	PyImGui.separator()
	PyImGui.spacing()

	accounts = _collect_accounts()
	selected_entry, selected_idx = _resolve_selected_account(accounts)

	if not accounts:
		PyImGui.text_disabled("No accounts found in Shared Memory.")
	else:
		labels = [entry.label for entry in accounts]
		PyImGui.push_item_width(320)
		new_idx = PyImGui.combo("Account", selected_idx, labels)
		PyImGui.pop_item_width()

		if 0 <= new_idx < len(accounts) and new_idx != selected_idx:
			selected_entry = accounts[new_idx]
			_selected_account_email = selected_entry.email
			selected_idx = new_idx

		if selected_entry:
			PyImGui.spacing()
			# Draw the edit window first so target/condition edits are applied before rendering the table.
			_draw_edit_window()
			entries = _collect_skillbar_entries(selected_entry.account)
			if entries:
				_draw_skill_table(entries)
			else:
				PyImGui.text_disabled("No skill data for this account.")
		else:
			PyImGui.text_disabled("No selection available.")

	PyImGui.spacing()
	PyImGui.text_colored("Use with Caution: Modifying skill conditions can lead to unintended consequences. Always review changes before applying.", Color(255, 0, 0, 255).to_tuple_normalized())
	PyImGui.text_colored("You need to reload the widgets to apply changes to HeroAI", Color(255, 0, 0, 255).to_tuple_normalized())

	window_module.process_window()
	window_module.end()


def main() -> None:
	try:
		_draw_window()
	except Exception as exc:
		Py4GW.Console.Log(MODULE_NAME, f"Error in main: {exc}", Py4GW.Console.MessageType.Error)


def tooltip():
	PyImGui.begin_tooltip()

	title_color = Color(255, 200, 100, 255)
	ImGui.push_font("Regular", 20)
	PyImGui.text_colored("HeroAI Skill Editor", title_color.to_tuple_normalized())
	ImGui.pop_font()
	PyImGui.spacing()
	PyImGui.separator()
	PyImGui.spacing()

	PyImGui.text("Displays the current skillbar with all HeroAI conditions.")
	PyImGui.text("Each skill includes the icon, name, and set checks.")
	PyImGui.spacing()

	PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
	PyImGui.bullet_text("Live overview of the eight skill slots")
	PyImGui.bullet_text("Account selection via Shared Memory dropdown")
	PyImGui.bullet_text("All HeroAI conditions per skill")
	PyImGui.spacing()
	PyImGui.separator()
	PyImGui.spacing()

	PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
	PyImGui.bullet_text("Developed by sch0l0ka")

	PyImGui.end_tooltip()


if __name__ == "__main__":
	main()
