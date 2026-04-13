import json
import os

from Py4GWCoreLib import (
	Agent,
	AgentArray,
	Color,
	GLOBAL_CACHE,
	ImGui,
	Map,
	Player,
	Py4GW,
	Routines,
	ThrottledTimer,
	UIManager,
	Utils,
)
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
import PyImGui
import PyInventory

MODULE_NAME = "Dhuum Helper"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# Keep this helper very cheap while idle.
_CHECK_TIMER = ThrottledTimer(750)
_CHECK_TIMER.Reset()

_DIALOG_COOLDOWN_TIMER = ThrottledTimer(2500)
_DIALOG_COOLDOWN_TIMER.Reset()

_armor_written_this_map: bool = False

_EQUIPPED_ARMOR_FILE = os.path.join(
	Py4GW.Console.get_projects_path(), "Widgets", "Config", "EquippedArmor.json"
)


def _write_equipped_armor_json() -> None:
	try:
		email = Player.GetAccountEmail()
		if not email:
			return

		_ARMOR_SLOTS = {2, 3, 4, 5, 6}  # Head, Chest, Hands, Legs, Feet
		bag = PyInventory.Bag(22, "Equipped_Items")
		slots: dict[str, int] = {}
		for item in bag.GetItems():
			item_id  = int(getattr(item, "item_id",  0) or 0)
			model_id = int(getattr(item, "model_id", 0) or 0)
			slot     = int(getattr(item, "slot",     0) or 0)
			if item_id == 0 or slot not in _ARMOR_SLOTS:
				continue
			slots[str(slot)] = model_id

		# Read existing file, merge this account's entry, write back atomically.
		all_armor: dict = {}
		if os.path.exists(_EQUIPPED_ARMOR_FILE):
			with open(_EQUIPPED_ARMOR_FILE, "r") as f:
				all_armor = json.load(f)

		# Migrate old flat format {"2": 123} -> {"normal": {"2": 123}, "sacrifice": {}}
		existing = all_armor.get(email, {})
		if not isinstance(existing, dict) or "normal" not in existing:
			old_slots = {k: v for k, v in existing.items() if isinstance(k, str) and k.isdigit()}
			existing = {"normal": old_slots, "sacrifice": {}}

		# Skip writing if sacrifice armor is currently equipped to avoid overwriting
		# the normal armor configuration with sacrifice model IDs.
		saved_sacrifice = existing.get("sacrifice") or {}
		sacrifice_model_ids = {v for v in saved_sacrifice.values() if v != 0}
		current_model_ids = set(slots.values())
		if sacrifice_model_ids and sacrifice_model_ids.issubset(current_model_ids):
			Py4GW.Console.Log(MODULE_NAME, "Armor write skipped - sacrifice armor is equipped.", Py4GW.Console.MessageType.Info)
			return

		existing["normal"] = slots
		all_armor[email] = existing

		tmp_path = _EQUIPPED_ARMOR_FILE + ".tmp"
		with open(tmp_path, "w") as f:
			json.dump(all_armor, f, indent=2)
		os.replace(tmp_path, _EQUIPPED_ARMOR_FILE)
	except Exception as e:
		Py4GW.Console.Log(MODULE_NAME, f"Armor write error: {e}", Py4GW.Console.MessageType.Warning)

_TARGET_NPC_NAME = "Mayor Alegheri"
_TARGET_BUFF_NAME = "Curse of Dhuum"
_NEARBY_NPC_RADIUS = 2000.0
_HEROAI_WIDGET_NAME = "HeroAI"
_CUSTOM_BEHAVIOR_WIDGET_NAMES = (
	"CustomBehaviors",
	"Custom Behavior",
	"Custom Behaviors: Utility AI",
)

_buff_skill_id = 0
_warned_missing_skill = False
_handled_current_buff = False
_interaction_running = False

_MAX_NPC_FIND_RETRIES = 10   # × 1 s  → up to 10 s waiting for NPC to appear
_MAX_MOVE_RETRIES     = 8    # × 1.5 s → up to 12 s to reach the NPC
_MAX_DIALOG_RETRIES   = 8    # × 2 s  → up to 16 s for dialog to open
_INTERACT_CLOSE_RANGE = 500.0


def _is_any_widget_enabled(*widget_names: str) -> bool:
	try:
		widget_handler = get_widget_handler()
		return any(bool(widget_handler.is_widget_enabled(name)) for name in widget_names)
	except Exception:
		return False


def _disable_combat_widgets_for_dialog() -> dict:
	"""Disable HeroAI widget for dialog (HeroAI-only accounts).
	CB movement is handled separately via _toggle_local_cb_movement()."""
	state = {
		"heroai_was_enabled": False,
		"custom_enabled_names": [],
	}

	try:
		widget_handler = get_widget_handler()

		heroai_enabled = bool(widget_handler.is_widget_enabled(_HEROAI_WIDGET_NAME))
		if heroai_enabled:
			widget_handler.disable_widget(_HEROAI_WIDGET_NAME)
			state["heroai_was_enabled"] = True
			Py4GW.Console.Log(
				MODULE_NAME,
				"Temporarily disabled HeroAI widget for Dhuum dialog.",
				Py4GW.Console.MessageType.Info,
			)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Failed to disable HeroAI widget before dialog: {ex}",
			Py4GW.Console.MessageType.Warning,
		)

	return state


def _restore_combat_widgets_after_dialog(state: dict) -> None:
	if not isinstance(state, dict):
		return

	try:
		widget_handler = get_widget_handler()

		if bool(state.get("heroai_was_enabled", False)) and not bool(widget_handler.is_widget_enabled(_HEROAI_WIDGET_NAME)):
			widget_handler.enable_widget(_HEROAI_WIDGET_NAME)
			Py4GW.Console.Log(
				MODULE_NAME,
				"Restored HeroAI widget state after Dhuum dialog.",
				Py4GW.Console.MessageType.Info,
			)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Failed to restore HeroAI widget after dialog: {ex}",
			Py4GW.Console.MessageType.Warning,
		)


def _toggle_local_cb_movement(enabled: bool) -> None:
	"""Enable/disable ALL movement-issuing CB utility skills on the local
	instance: following skills AND automover/botting skills that reposition
	the player.  Does NOT touch shared memory — only this account is affected."""
	try:
		from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
		behavior = CustomBehaviorLoader().custom_combat_behavior
		if behavior is None:
			return
		_MOVEMENT_SKILL_NAMES = (
			"follow_party_leader",
			"follow_flag",
			"move_to_party_member_if_in_aggro",
			"move_to_enemy_if_close_enough",
			"move_to_party_member_if_dead",
			"wait_if_in_aggro",
			"move_to_distant_chest_if_path_exists",
		)
		_MOVEMENT_CLASS_NAMES = (
			"FollowPartyLeaderUtility",
			"FollowFlagUtility",
			"MoveToPartyMemberIfInAggroUtility",
			"MoveToEnemyIfCloseEnoughUtility",
			"MoveToPartyMemberIfDeadUtility",
			"WaitIfInAggroUtility",
			"MoveToDistantChestIfPathExistsUtility",
		)
		for utility in behavior.get_skills_final_list():
			skill_name = getattr(getattr(utility, "custom_skill", None), "skill_name", None)
			if skill_name in _MOVEMENT_SKILL_NAMES or utility.__class__.__name__ in _MOVEMENT_CLASS_NAMES:
				utility.is_enabled = enabled
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Local CB movement {'enabled' if enabled else 'disabled'}.",
			Py4GW.Console.MessageType.Info,
		)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Failed to toggle local CB movement: {ex}",
			Py4GW.Console.MessageType.Warning,
		)


def _refresh_custom_behavior_after_skillbar_change() -> None:
	try:
		from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
		loader = CustomBehaviorLoader()

		# Local refresh sequence without private internals.
		if loader.custom_combat_behavior is not None:
			try:
				loader.custom_combat_behavior.disable()
			except Exception:
				pass

		loader.refresh_custom_behavior_candidate()
		loader.initialize_custom_behavior_candidate()
		behavior_name = loader.custom_combat_behavior.__class__.__name__ if loader.custom_combat_behavior is not None else "None"
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Custom Behavior refreshed after Dhuum dialog. Active behavior: {behavior_name}",
			Py4GW.Console.MessageType.Info,
		)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Custom Behavior refresh failed: {ex}",
			Py4GW.Console.MessageType.Warning,
		)


def _refresh_heroai_build_after_skillbar_change() -> None:
	try:
		from Widgets.Automation.Multiboxing import HeroAI as HeroAI_Widget

		# Force HeroAI build contract to be re-evaluated after the dialog skillbar swap.
		HeroAI_Widget.heroai_build.ClearBuildContract()
		HeroAI_Widget.build_contract_map_signature = None

		try:
			HeroAI_Widget.heroai_build.EnsureBuildContract(HeroAI_Widget.cached_data)
		except Exception:
			# If the widget is not fully initialized yet, it will rebuild on next normal tick.
			pass

		contract = HeroAI_Widget.heroai_build.GetBuildContract()
		contract_name = contract.build_name if contract is not None else "None"
		Py4GW.Console.Log(
			MODULE_NAME,
			f"HeroAI build refreshed after Dhuum dialog. Active build: {contract_name}",
			Py4GW.Console.MessageType.Info,
		)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"HeroAI build refresh failed: {ex}",
			Py4GW.Console.MessageType.Warning,
		)


def _refresh_active_combat_widget_after_skillbar_change() -> None:
	# Execute only the relevant refresh path for the currently active combat widget.
	heroai_enabled = _is_any_widget_enabled(_HEROAI_WIDGET_NAME)
	custom_behavior_enabled = _is_any_widget_enabled(*_CUSTOM_BEHAVIOR_WIDGET_NAMES)

	if heroai_enabled and not custom_behavior_enabled:
		_refresh_heroai_build_after_skillbar_change()
		return

	if custom_behavior_enabled and not heroai_enabled:
		_refresh_custom_behavior_after_skillbar_change()
		return

	if heroai_enabled and custom_behavior_enabled:
		Py4GW.Console.Log(
			MODULE_NAME,
			"Both HeroAI and CustomBehaviors are enabled. Skipping refresh to avoid wrong re-initialization.",
			Py4GW.Console.MessageType.Warning,
		)
		return

	Py4GW.Console.Log(
		MODULE_NAME,
		"No supported combat widget enabled (HeroAI/CustomBehaviors). Skipping build refresh.",
		Py4GW.Console.MessageType.Warning,
	)


def tooltip():
	PyImGui.begin_tooltip()
	title_color = Color(255, 200, 100, 255)
	ImGui.push_font("Regular", 20)
	PyImGui.text_colored("Dhuum Helper", title_color.to_tuple_normalized())
	ImGui.pop_font()
	PyImGui.spacing()
	PyImGui.separator()
	PyImGui.text("Auto rez at Dhuum for Multiboxaccounts")
	PyImGui.end_tooltip()


def _resolve_buff_skill_id() -> int:
	global _warned_missing_skill

	candidates = (
		_TARGET_BUFF_NAME,
		_TARGET_BUFF_NAME.replace(" ", "_"),
	)

	for name in candidates:
		try:
			skill_id = int(GLOBAL_CACHE.Skill.GetID(name))
		except Exception:
			skill_id = 0
		if skill_id > 0:
			return skill_id

	if not _warned_missing_skill:
		_warned_missing_skill = True
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Could not resolve buff skill id for '{_TARGET_BUFF_NAME}'.",
			Py4GW.Console.MessageType.Warning,
		)

	return 0


def _find_nearby_max() -> int:
	px, py = Player.GetXY()
	nearest_id = 0
	nearest_dist = 999999.0

	for agent_id in AgentArray.GetNPCMinipetArray():
		name = (Agent.GetNameByID(agent_id) or "").strip().lower()
		if name != _TARGET_NPC_NAME.lower():
			continue

		ax, ay = Agent.GetXY(agent_id)
		dist = Utils.Distance((px, py), (ax, ay))
		if dist > _NEARBY_NPC_RADIUS:
			continue
		if dist < nearest_dist:
			nearest_id = int(agent_id)
			nearest_dist = float(dist)

	return nearest_id


def _is_valid_target_npc(agent_id: int) -> bool:
	if int(agent_id) <= 0:
		return False

	try:
		npc_ids = AgentArray.GetNPCMinipetArray()
		if int(agent_id) not in {int(npc_id) for npc_id in npc_ids}:
			return False

		name = (Agent.GetNameByID(agent_id) or "").strip().lower()
		return name == _TARGET_NPC_NAME.lower()
	except Exception:
		return False


def _resolve_valid_target_npc(candidate_id: int) -> int:
	if _is_valid_target_npc(candidate_id):
		return int(candidate_id)
	return _find_nearby_max()


def _coro_interact_and_dialog(target_npc: int):
	global _interaction_running
	combat_widget_state = None
	widgets_temporarily_disabled = False

	try:
		# ── Step 1: Find NPC ────────────────────────────────────────────
		for attempt in range(_MAX_NPC_FIND_RETRIES):
			target_npc = _resolve_valid_target_npc(target_npc)
			if target_npc > 0:
				break
			Py4GW.Console.Log(
				MODULE_NAME,
				f"NPC not found, retrying {attempt + 1}/{_MAX_NPC_FIND_RETRIES} ...",
				Py4GW.Console.MessageType.Info,
			)
			yield from Routines.Yield.wait(1000)
			target_npc = _resolve_valid_target_npc(0)

		if target_npc <= 0:
			Py4GW.Console.Log(
				MODULE_NAME,
				"NPC not found after all retries - aborting.",
				Py4GW.Console.MessageType.Warning,
			)
			return

		# Disable HeroAI widget and ALL local CB movement utilities while approaching
		# and interacting with the NPC so movement commands don't pull us away.
		combat_widget_state = _disable_combat_widgets_for_dialog()
		widgets_temporarily_disabled = True
		_toggle_local_cb_movement(False)

		# ── Step 2: Move to NPC ─────────────────────────────────────────
		target_npc = _resolve_valid_target_npc(target_npc)
		if target_npc <= 0:
			Py4GW.Console.Log(
				MODULE_NAME,
				"NPC disappeared before targeting - aborting.",
				Py4GW.Console.MessageType.Warning,
			)
			return

		Player.ChangeTarget(target_npc)
		yield from Routines.Yield.wait(100)

		for attempt in range(_MAX_MOVE_RETRIES):
			target_npc = _resolve_valid_target_npc(target_npc)
			if target_npc <= 0:
				Py4GW.Console.Log(
					MODULE_NAME,
					"NPC disappeared while moving - aborting.",
					Py4GW.Console.MessageType.Warning,
				)
				return

			try:
				ax, ay = Agent.GetXY(target_npc)
			except Exception:
				Py4GW.Console.Log(
					MODULE_NAME,
					"Failed to get NPC position - retrying.",
					Py4GW.Console.MessageType.Warning,
				)
				yield from Routines.Yield.wait(300)
				continue

			px, py = Player.GetXY()
			if Utils.Distance((px, py), (ax, ay)) <= _INTERACT_CLOSE_RANGE:
				break
			Py4GW.Console.Log(
				MODULE_NAME,
				f"Moving to NPC, attempt {attempt + 1}/{_MAX_MOVE_RETRIES} ...",
				Py4GW.Console.MessageType.Info,
			)
			Player.Move(ax, ay)
			yield from Routines.Yield.wait(1500)
			# Re-resolve NPC id in case the agent slot changed after moving
			new_id = _resolve_valid_target_npc(target_npc)
			if new_id > 0:
				target_npc = new_id
				Player.ChangeTarget(target_npc)

		# ── Step 3: Interact and send dialog ────────────────────────────
		dialog_sent = False
		for attempt in range(_MAX_DIALOG_RETRIES):
			target_npc = _resolve_valid_target_npc(target_npc)
			if target_npc <= 0:
				Py4GW.Console.Log(
					MODULE_NAME,
					"NPC disappeared before interaction - aborting.",
					Py4GW.Console.MessageType.Warning,
				)
				return

			Py4GW.Console.Log(
				MODULE_NAME,
				f"Interacting with NPC, attempt {attempt + 1}/{_MAX_DIALOG_RETRIES} ...",
				Py4GW.Console.MessageType.Info,
			)
			Player.ChangeTarget(target_npc)
			yield from Routines.Yield.wait(100)
			Player.Interact(target_npc)
			yield from Routines.Yield.wait(2000)

			if not UIManager.IsNPCDialogVisible():
				continue

			# Primary send path
			Player.SendDialog(0x84)
			yield from Routines.Yield.wait(150)

			# Fallback path
			if UIManager.IsNPCDialogVisible():
				UIManager.ClickDialogButton(0x84)
				yield from Routines.Yield.wait(150)

			dialog_sent = True
			break

		if not dialog_sent:
			Py4GW.Console.Log(
				MODULE_NAME,
				"Failed to send dialog 0x84: NPC dialog did not open in time.",
				Py4GW.Console.MessageType.Warning,
			)
			return

		# Skillbar may change after this dialog - trigger CB re-detection
		yield from Routines.Yield.wait(800)
		

		# Move to safe position after resurrection
		yield from Routines.Yield.wait(2000)
		Player.Move(-14374, 17261)

		if widgets_temporarily_disabled and combat_widget_state is not None:
			_restore_combat_widgets_after_dialog(combat_widget_state)
			_toggle_local_cb_movement(True)
			widgets_temporarily_disabled = False

		_refresh_active_combat_widget_after_skillbar_change()
		_DIALOG_COOLDOWN_TIMER.Reset()
	finally:
		if widgets_temporarily_disabled and combat_widget_state is not None:
			_restore_combat_widgets_after_dialog(combat_widget_state)
			_toggle_local_cb_movement(True)
		_interaction_running = False


def main():
	global _buff_skill_id, _handled_current_buff, _interaction_running, _armor_written_this_map

	if not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
		_handled_current_buff = False
		_armor_written_this_map = False
		return

	if not _armor_written_this_map:
		_write_equipped_armor_json()
		_armor_written_this_map = True

	if not _CHECK_TIMER.IsExpired():
		return
	_CHECK_TIMER.Reset()

	if _buff_skill_id <= 0:
		_buff_skill_id = _resolve_buff_skill_id()
		if _buff_skill_id <= 0:
			return

	player_id = Player.GetAgentID()
	has_target_buff = bool(GLOBAL_CACHE.Effects.HasEffect(player_id, _buff_skill_id))

	if not has_target_buff:
		_handled_current_buff = False
		return

	if _handled_current_buff or _interaction_running:
		return

	if not _DIALOG_COOLDOWN_TIMER.IsExpired():
		return

	max_id = _find_nearby_max()
	if max_id <= 0:
		return

	_interaction_running = True
	_handled_current_buff = True
	GLOBAL_CACHE.Coroutines.append(_coro_interact_and_dialog(max_id))


if __name__ == "__main__":
	main()
