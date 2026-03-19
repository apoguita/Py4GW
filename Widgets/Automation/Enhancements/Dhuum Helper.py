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
	Utils,
)
import PyImGui

MODULE_NAME = "Dhuum Helper"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# Keep this helper very cheap while idle.
_CHECK_TIMER = ThrottledTimer(750)
_CHECK_TIMER.Reset()

_DIALOG_COOLDOWN_TIMER = ThrottledTimer(2500)
_DIALOG_COOLDOWN_TIMER.Reset()

_TARGET_NPC_NAME = "Mayor Alegheri"
_TARGET_BUFF_NAME = "Curse of Dhuum"
_NEARBY_NPC_RADIUS = 2000.0

_buff_skill_id = 0
_warned_missing_skill = False
_handled_current_buff = False
_interaction_running = False


def _refresh_custom_behavior_after_skillbar_change() -> None:
	try:
		from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
		CustomBehaviorLoader().refresh_custom_behavior_candidate()
		Py4GW.Console.Log(
			MODULE_NAME,
			"Custom Behavior refresh requested after Dhuum dialog.",
			Py4GW.Console.MessageType.Info,
		)
	except Exception as ex:
		Py4GW.Console.Log(
			MODULE_NAME,
			f"Custom Behavior refresh failed: {ex}",
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


def _coro_interact_and_dialog(target_npc: int):
	global _interaction_running

	try:
		if target_npc <= 0:
			return

		Player.ChangeTarget(target_npc)
		yield from Routines.Yield.wait(100)
		Player.Interact(target_npc)
		yield from Routines.Yield.wait(450)
		Player.SendDialog(0x84)
		# Skillbar can change after this dialog; trigger CB re-detection.
		yield from Routines.Yield.wait(800)
		_refresh_custom_behavior_after_skillbar_change()
		_DIALOG_COOLDOWN_TIMER.Reset()
	finally:
		_interaction_running = False


def main():
	global _buff_skill_id, _handled_current_buff, _interaction_running

	if not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
		_handled_current_buff = False
		return

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
