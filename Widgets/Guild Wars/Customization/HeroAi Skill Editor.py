from __future__ import annotations

import re
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Any, List, Optional, Set

import PyImGui
import Py4GW

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Color, Range, Player
from HeroAI.custom_skill import CustomSkillClass
from HeroAI.custom_skill_src.skill_types import CastConditions, CustomSkill
from HeroAI.types import Skilltarget

MODULE_NAME = "HeroAI Skill Editor"

window_module = ImGui.WindowModule(
	MODULE_NAME,
	window_name="HeroAI Skillbar",
	window_size=(700, 700),
	window_flags=PyImGui.WindowFlags.AlwaysAutoResize,
	can_close=True,
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
_CONDITION_OPTIONS: tuple[str, ...] = tuple(sorted(DEFAULT_CONDITION_VALUES.keys(), key=lambda name: name.lower()))
_ACTIVE_STATE_COLOR = (0.3, 0.9, 0.4, 1.0)
_SKILL_SOURCE_INDEX: dict = {}


class ConditionSummary:
	__slots__ = ("name", "text")

	def __init__(self, name: str, text: str) -> None:
		self.name = name
		self.text = text


class SkillEditSnapshot:
	__slots__ = ("slot", "skill_id", "name", "target", "target_value", "active_conditions", "condition_values")

	def __init__(
		self,
		slot: int,
		skill_id: int,
		name: str,
		target: str,
		target_value: Optional[int],
		active_conditions: Set[str],
		condition_values: dict[str, Any],
	) -> None:
		self.slot = slot
		self.skill_id = skill_id
		self.name = name
		self.target = target
		self.target_value = target_value
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
		return False, "Skill source modification is not yet supported."
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


def _handle_target_change(row: SkillRow, new_enum: Skilltarget) -> None:
	if row.skill_id == 0:
		return
	success, message = _persist_skill_target(row.skill_id, new_enum)
	message_type = Py4GW.Console.MessageType.Info if success else Py4GW.Console.MessageType.Error
	Py4GW.Console.Log(MODULE_NAME, message, message_type)
	if not success:
		return
	global custom_skill_provider
	custom_skill_provider = CustomSkillClass()
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
		self.active_conditions = active_conditions
		self.condition_values = condition_values
		self.special = special
		self.special_target = special_target


def _prettify_name(name: str) -> str:
	spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("_", " ")
	return spaced.strip()


def _condition_changed(name: str, value) -> bool:
	default_value = DEFAULT_CONDITION_VALUES.get(name)
	if isinstance(value, float):
		if default_value is None:
			return True
		return abs(value - float(default_value)) > EPSILON
	if isinstance(value, list):
		return len(value) > 0
	return value != default_value


def _format_condition_value(name: str, value) -> str:
	pretty_name = _prettify_name(name)

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


def _describe_conditions(skill: Optional[CustomSkill]) -> tuple[List[str], Set[str], dict[str, Any]]:
	if skill is None or not skill.SkillID:
		return [], set(), {}

	summary: List[str] = []
	active_names: Set[str] = set()
	active_values: dict[str, Any] = {}
	for name, value in vars(skill.Conditions).items():
		if name not in DEFAULT_CONDITION_VALUES:
			continue
		if not _condition_changed(name, value):
			continue
		formatted = _format_condition_value(name, value)
		if formatted:
			summary.append(formatted)
			active_names.add(name)
			active_values[name] = value
	return summary, active_names, active_values


def _safe_get_custom_skill(skill_id: int) -> Optional[CustomSkill]:
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
		display_name = char_name if char_name else email or "Unknown"
		if char_name and email and char_name.lower() not in email.lower():
			label = f"{char_name} ({email})"
		else:
			label = display_name
		entries.append(AccountEntry(label=label, email=email, character=display_name, account=account))

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


def _collect_skillbar_entries(account) -> List[SkillRow]:
	if account is None:
		return []

	player_data = getattr(account, "PlayerData", None)
	skillbar_data = getattr(player_data, "SkillbarData", None)
	if skillbar_data is None or not hasattr(skillbar_data, "Skills"):
		return []

	entries: List[SkillRow] = []
	for idx in range(MAX_SKILL_SLOTS):
		slot = idx + 1
		try:
			skill_struct = skillbar_data.Skills[idx]
		except Exception:
			skill_struct = None

		skill_id = int(getattr(skill_struct, "Id", 0)) if skill_struct else 0
		if not skill_id:
			entries.append(SkillRow(slot, 0, "Empty Slot", None, [], "--", None, set(), {}, None, None))
			continue

		skill_name = GLOBAL_CACHE.Skill.GetName(skill_id) or f"Skill {skill_id}"
		skill_name = skill_name.replace("_", " ")
		custom_skill = _safe_get_custom_skill(skill_id)
		conditions, active_conditions, condition_values = _describe_conditions(custom_skill)
		target = _format_target(custom_skill)
		special = _get_special_behavior(skill_id)
		special_target = _get_special_target_info(skill_id)
		texture_rel = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
		texture_path = _texture_full_path(texture_rel)
		target_value = custom_skill.TargetAllegiance if custom_skill else None
		entries.append(
			SkillRow(
				slot,
				skill_id,
				skill_name,
				texture_path,
				conditions,
				target,
				target_value,
				active_conditions,
				condition_values,
				special,
				special_target,
			)
		)

	return entries


def _format_target(skill: Optional[CustomSkill]) -> str:
	if skill is None:
		return "Unknown"
	try:
		enum_value = Skilltarget(skill.TargetAllegiance)
		return enum_value.name.replace("_", " ")
	except ValueError:
		return str(skill.TargetAllegiance)


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
		PyImGui.text_disabled(f"ID {row.skill_id}")
	else:
		PyImGui.text_disabled("Kein Skill")
	PyImGui.end_group()


def _draw_target_cell(row: SkillRow) -> None:
	PyImGui.text(row.target)
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
	_edit_snapshot = SkillEditSnapshot(
		row.slot,
		row.skill_id,
		row.name,
		row.target,
		row.target_value,
		row.active_conditions,
		row.condition_values,
	)
	_edit_window_open = True


def _render_target_list(selected_value: Optional[int], fallback_label: str) -> None:
	inner_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if not PyImGui.begin_table("##target_inner_table", 2, inner_flags, 0, 0):
		PyImGui.text_disabled("Targets could not be loaded.")
		return
	PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthStretch, 0)
	PyImGui.table_setup_column("Active", PyImGui.TableColumnFlags.WidthFixed, 70)
	PyImGui.table_headers_row()
	for option in _TARGET_OPTIONS:
		PyImGui.table_next_row()
		label = option.name.replace("_", " ")
		is_active = selected_value == option.value
		if selected_value is None:
			is_active = label.lower() == fallback_label
		PyImGui.table_set_column_index(0)
		PyImGui.selectable(
			f"{label}##target_option_{option.value}",
			is_active,
			0,
			(0.0, 0.0),
		)
		PyImGui.table_set_column_index(1)
		if is_active:
			PyImGui.text_colored("True", _ACTIVE_STATE_COLOR)
		else:
			PyImGui.text_disabled("False")
	PyImGui.end_table()


def _render_condition_list(active_conditions: Set[str], condition_values: dict[str, Any]) -> None:
	inner_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if not PyImGui.begin_table("##condition_inner_table", 2, inner_flags, 0, 0):
		PyImGui.text_disabled("Conditions could not be loaded.")
		return
	PyImGui.table_setup_column("Condition", PyImGui.TableColumnFlags.WidthStretch, 0)
	PyImGui.table_setup_column("Active Value", PyImGui.TableColumnFlags.WidthFixed, 120)
	PyImGui.table_headers_row()
	for condition_name in _CONDITION_OPTIONS:
		PyImGui.table_next_row()
		pretty = _prettify_name(condition_name)
		is_condition_active = condition_name in active_conditions
		PyImGui.table_set_column_index(0)
		PyImGui.selectable(
			f"{pretty}##condition_option_{condition_name}",
			is_condition_active,
			0,
			(0.0, 0.0),
		)
		PyImGui.table_set_column_index(1)
		if is_condition_active:
			value = condition_values.get(condition_name)
			PyImGui.text_colored(_format_condition_raw_value(value), _ACTIVE_STATE_COLOR)
		else:
			PyImGui.text_disabled("-")
	PyImGui.end_table()


def _draw_edit_window() -> None:
	global _edit_window_open, _edit_snapshot
	if not _edit_window_open or _edit_snapshot is None:
		return
	opened = PyImGui.begin("Skill Editor", PyImGui.WindowFlags.AlwaysAutoResize)
	if not opened:
		PyImGui.end()
		_edit_window_open = False
		return
	PyImGui.text(f"Slot {_edit_snapshot.slot}")
	PyImGui.text(f"Skill: {_edit_snapshot.name} (ID {_edit_snapshot.skill_id})")
	PyImGui.text(f"Current Target: {_edit_snapshot.target}")
	PyImGui.spacing()
	flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if PyImGui.begin_table("##edit_target_options", 2, flags, 0, 0):
		PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthStretch, 0)
		PyImGui.table_setup_column("Conditions", PyImGui.TableColumnFlags.WidthStretch, 0)
		PyImGui.table_headers_row()
		PyImGui.table_next_row()
		PyImGui.table_set_column_index(0)
		_render_target_list(_edit_snapshot.target_value, (_edit_snapshot.target or "").lower())
		PyImGui.table_set_column_index(1)
		_render_condition_list(_edit_snapshot.active_conditions, _edit_snapshot.condition_values)
		PyImGui.end_table()
	else:
		PyImGui.text_disabled("Targets could not be loaded.")
	PyImGui.spacing()
	if PyImGui.button("Close Window"):
		_edit_window_open = False
	PyImGui.end()


def _draw_condition_cell(row: SkillRow) -> None:
	if row.conditions:
		for condition in row.conditions:
			PyImGui.bullet_text(condition)
	else:
		PyImGui.text("No Conditions")

	if row.special:
		if row.conditions:
			PyImGui.spacing()
		PyImGui.text("Special Conditions:")
		for line in row.special.splitlines():
			clean = line.strip()
			if clean:
				PyImGui.bullet_text(clean)


def _draw_skill_table(entries: List[SkillRow]) -> None:
	flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp
	if PyImGui.begin_table("##HeroAiSkillTable", 5, flags, 0, 0):
		PyImGui.table_setup_column("Slot", PyImGui.TableColumnFlags.WidthFixed, 20)
		PyImGui.table_setup_column("Skill", PyImGui.TableColumnFlags.WidthFixed, 250)
		PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthFixed, 250)
		PyImGui.table_setup_column("Conditions", PyImGui.TableColumnFlags.WidthStretch, 0)
		PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.WidthFixed, 80)
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

	PyImGui.text("HeroAI Skillbars")
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
			PyImGui.text_disabled(f"Character: {selected_entry.character}")
			PyImGui.spacing()
			entries = _collect_skillbar_entries(selected_entry.account)
			if entries:
				_draw_skill_table(entries)
			else:
				PyImGui.text_disabled("No skill data for this account.")
		else:
			PyImGui.text_disabled("No selection available.")

	_draw_edit_window()

	PyImGui.spacing()
	PyImGui.text_disabled("Source: HeroAI custom_skill_src conditions + Shared Memory Skillbars")

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
