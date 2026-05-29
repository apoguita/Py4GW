import time as _time

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
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree as _BT
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as _RoutinesBT
import PyImGui

# ── Module identity ───────────────────────────────────────────────────────────

MODULE_NAME = "Dhuum Helper"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# ── Constants ─────────────────────────────────────────────────────────────────

_TARGET_NPC_NAME       = "Mayor Alegheri"
_TARGET_NPC_NAME_LOWER = _TARGET_NPC_NAME.lower()
_TARGET_BUFF_NAME      = "Curse of Dhuum"
_NEARBY_NPC_RADIUS     = 2000.0
_INTERACT_CLOSE_RANGE  = 500.0

# ── Timers ────────────────────────────────────────────────────────────────────

_CHECK_TIMER = ThrottledTimer(3000)
_CHECK_TIMER.Reset()

_DIALOG_COOLDOWN_TIMER = ThrottledTimer(2500)
_DIALOG_COOLDOWN_TIMER.Reset()

# ── Runtime state ─────────────────────────────────────────────────────────────

_buff_skill_id: int        = 0
_warned_missing_skill: bool = False
_handled_current_buff: bool = False
_interaction_tree: _BT | None = None

# ── Following helpers ─────────────────────────────────────────────────────────

def _pause_following() -> None:
	"""Set Following=False so the follower stops chasing the leader during the dialog."""
	try:
		email = Player.GetAccountEmail()
		if email:
			GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'Following', False)
			Py4GW.Console.Log(MODULE_NAME, "Following paused for Dhuum dialog.", Py4GW.Console.MessageType.Info)
	except Exception as ex:
		Py4GW.Console.Log(MODULE_NAME, f"Failed to pause following: {ex}", Py4GW.Console.MessageType.Warning)


def _resume_following() -> None:
	"""Restore Following=True after the dialog interaction is complete."""
	try:
		email = Player.GetAccountEmail()
		if email:
			GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'Following', True)
			Py4GW.Console.Log(MODULE_NAME, "Following resumed after Dhuum dialog.", Py4GW.Console.MessageType.Info)
	except Exception as ex:
		Py4GW.Console.Log(MODULE_NAME, f"Failed to resume following: {ex}", Py4GW.Console.MessageType.Warning)

# ── HeroAI build refresh ──────────────────────────────────────────────────────

def _refresh_heroai_build() -> None:
	"""Force HeroAI to re-evaluate its build contract after the dialog skillbar swap."""
	try:
		from Widgets.Automation.Multiboxing import HeroAI as HeroAI_Widget

		HeroAI_Widget.heroai_build.ClearBuildContract()
		HeroAI_Widget.build_contract_map_signature = None

		try:
			HeroAI_Widget.heroai_build.EnsureBuildContract(HeroAI_Widget.cached_data)
		except Exception:
			pass  # Will rebuild on next normal tick if not ready yet.

		contract      = HeroAI_Widget.heroai_build.GetBuildContract()
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

# ── Widget entry points ───────────────────────────────────────────────────────

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

# ── Buff / skill resolution ───────────────────────────────────────────────────

def _resolve_buff_skill_id() -> int:
	global _warned_missing_skill

	for name in (_TARGET_BUFF_NAME, _TARGET_BUFF_NAME.replace(" ", "_")):
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

# ── NPC resolution ────────────────────────────────────────────────────────────

def _find_nearby_max() -> int:
	px, py      = Player.GetXY()
	nearest_id  = 0
	nearest_dist = 999999.0

	for agent_id in AgentArray.GetNPCMinipetArray():
		aid = int(agent_id)
		if not Agent.IsValid(aid):
			continue
		try:
			name = (Agent.GetNameByID(aid) or "").strip().lower()
		except Exception:
			continue
		if name != _TARGET_NPC_NAME_LOWER:
			continue

		ax, ay = Agent.GetXY(aid)
		dist   = Utils.Distance((px, py), (ax, ay))
		if dist > _NEARBY_NPC_RADIUS:
			continue
		if dist < nearest_dist:
			nearest_id   = aid
			nearest_dist = float(dist)

	return nearest_id


def _is_valid_target_npc(agent_id: int) -> bool:
	if int(agent_id) <= 0:
		return False
	try:
		npc_ids = AgentArray.GetNPCMinipetArray()
		if int(agent_id) not in {int(npc_id) for npc_id in npc_ids}:
			return False
		if not Agent.IsValid(int(agent_id)):
			return False
		name = (Agent.GetNameByID(int(agent_id)) or "").strip().lower()
		return name == _TARGET_NPC_NAME_LOWER
	except Exception:
		return False


def _resolve_valid_target_npc(candidate_id: int) -> int:
	if _is_valid_target_npc(candidate_id):
		return int(candidate_id)
	return _find_nearby_max()

# ── BT interaction tree ───────────────────────────────────────────────────────

def _cleanup_interaction() -> None:
	"""Resume following and clear target — called on both SUCCESS and FAILURE."""
	_resume_following()
	Player.ChangeTarget(0)


def _build_interaction_tree(initial_npc_id: int) -> _BT:
	"""
	One-shot BT for the Dhuum dialog interaction:
	  1. Wait until Mayor Alegheri is in range (up to 10 s).
	  2. Pause Following — follower stops running back to team, HeroAI stays active.
	  3. Move to NPC (up to 12 s).
	  4. Interact until the NPC dialog opens (up to 16 s).
	  5. Send dialog 0x84 and clear target (aftercast 800 ms for skillbar swap).
	  6. Wait 2 s, then move to safe position.
	  7. Resume Following, refresh HeroAI build, reset cooldown.
	"""
	exec_state: dict = {
		'npc_id':         initial_npc_id,
		'move_timer':     ThrottledTimer(1500),
		'interact_timer': ThrottledTimer(2000),
		'move_deadline':  None,
		'dialog_deadline': None,
	}
	exec_state['move_timer'].Reset()
	exec_state['interact_timer'].Reset()

	# ── Step 1 ─────────────────────────────────────────────────────────────────
	def _find_npc_condition() -> bool:
		npc_id = _resolve_valid_target_npc(exec_state['npc_id'])
		if npc_id > 0:
			exec_state['npc_id'] = npc_id
			return True
		exec_state['npc_id'] = 0
		return False

	# ── Step 2 ─────────────────────────────────────────────────────────────────
	def _pause_following_step(_node: _BT.Node) -> _BT.NodeState:
		_pause_following()
		return _BT.NodeState.SUCCESS

	# ── Step 3 ─────────────────────────────────────────────────────────────────
	def _move_to_npc_tick(_node: _BT.Node) -> _BT.NodeState:
		now = _time.monotonic()
		if exec_state['move_deadline'] is None:
			exec_state['move_deadline'] = now + 12.0
		elif now >= exec_state['move_deadline']:
			Py4GW.Console.Log(MODULE_NAME, "Failed to reach NPC in time — aborting.", Py4GW.Console.MessageType.Warning)
			exec_state['move_deadline'] = None
			return _BT.NodeState.FAILURE

		npc_id = _resolve_valid_target_npc(exec_state['npc_id'])
		if npc_id <= 0:
			Py4GW.Console.Log(MODULE_NAME, "NPC disappeared while moving — aborting.", Py4GW.Console.MessageType.Warning)
			return _BT.NodeState.FAILURE
		exec_state['npc_id'] = npc_id

		try:
			ax, ay = Agent.GetXY(npc_id)
		except Exception:
			return _BT.NodeState.RUNNING

		px, py = Player.GetXY()
		if Utils.Distance((px, py), (ax, ay)) <= _INTERACT_CLOSE_RANGE:
			exec_state['move_deadline'] = None
			return _BT.NodeState.SUCCESS

		if exec_state['move_timer'].IsExpired():
			exec_state['move_timer'].Reset()
			Player.ChangeTarget(npc_id)
			Player.Move(ax, ay)
		return _BT.NodeState.RUNNING

	# ── Step 4 ─────────────────────────────────────────────────────────────────
	def _interact_until_dialog_tick(_node: _BT.Node) -> _BT.NodeState:
		if UIManager.IsNPCDialogVisible():
			exec_state['dialog_deadline'] = None
			return _BT.NodeState.SUCCESS

		now = _time.monotonic()
		if exec_state['dialog_deadline'] is None:
			exec_state['dialog_deadline'] = now + 16.0
		elif now >= exec_state['dialog_deadline']:
			Py4GW.Console.Log(MODULE_NAME, "Dialog did not open in time — aborting.", Py4GW.Console.MessageType.Warning)
			exec_state['dialog_deadline'] = None
			return _BT.NodeState.FAILURE

		npc_id = _resolve_valid_target_npc(exec_state['npc_id'])
		if npc_id <= 0:
			Py4GW.Console.Log(MODULE_NAME, "NPC disappeared before interaction — aborting.", Py4GW.Console.MessageType.Warning)
			return _BT.NodeState.FAILURE
		exec_state['npc_id'] = npc_id

		if exec_state['interact_timer'].IsExpired():
			exec_state['interact_timer'].Reset()
			Player.ChangeTarget(npc_id)
			Player.Interact(npc_id)
		return _BT.NodeState.RUNNING

	# ── Step 5 ─────────────────────────────────────────────────────────────────
	def _send_dialog_and_clear(_node: _BT.Node) -> _BT.NodeState:
		Player.SendDialog(0x84)
		if UIManager.IsNPCDialogVisible():
			UIManager.ClickDialogButton(0x84)
		Player.ChangeTarget(0)
		return _BT.NodeState.SUCCESS

	# ── Step 6 ─────────────────────────────────────────────────────────────────
	def _move_safe(_node: _BT.Node) -> _BT.NodeState:
		Player.Move(-14374, 17261)
		return _BT.NodeState.SUCCESS

	# ── Step 7 ─────────────────────────────────────────────────────────────────
	def _restore_and_finish(_node: _BT.Node) -> _BT.NodeState:
		_cleanup_interaction()
		_refresh_heroai_build()
		_DIALOG_COOLDOWN_TIMER.Reset()
		return _BT.NodeState.SUCCESS

	return _RoutinesBT.Composite.Sequence(
		_BT(_BT.WaitUntilNode(
			name='FindNPC',
			condition_fn=_find_npc_condition,
			throttle_interval_ms=500,
			timeout_ms=10_000,
		)),
		_BT(_BT.ActionNode(name='PauseFollowing',      action_fn=_pause_following_step,      aftercast_ms=100)),
		_BT(_BT.ActionNode(name='MoveToNPC',           action_fn=_move_to_npc_tick)),
		_BT(_BT.ActionNode(name='InteractUntilDialog', action_fn=_interact_until_dialog_tick)),
		_BT(_BT.ActionNode(name='SendDialog',          action_fn=_send_dialog_and_clear,     aftercast_ms=800)),
		_RoutinesBT.Player.Wait(duration_ms=2000),
		_BT(_BT.ActionNode(name='MoveSafe',            action_fn=_move_safe)),
		_BT(_BT.ActionNode(name='RestoreAndFinish',    action_fn=_restore_and_finish)),
		name='DhuumHelperInteraction',
	)

# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
	global _buff_skill_id, _handled_current_buff, _interaction_tree

	if not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
		_handled_current_buff = False
		if _interaction_tree is not None:
			_interaction_tree.reset()
			_cleanup_interaction()
			_interaction_tree = None
		return

	# Tick the active interaction tree every frame until it finishes.
	if _interaction_tree is not None:
		result = _interaction_tree.tick()
		if result != _BT.NodeState.RUNNING:
			if result == _BT.NodeState.FAILURE:
				_cleanup_interaction()
			_interaction_tree = None
		return

	# Throttled idle check — only search for triggers every 750 ms.
	if not _CHECK_TIMER.IsExpired():
		return
	_CHECK_TIMER.Reset()

	if _buff_skill_id <= 0:
		_buff_skill_id = _resolve_buff_skill_id()
		if _buff_skill_id <= 0:
			return

	player_id      = Player.GetAgentID()
	has_target_buff = bool(GLOBAL_CACHE.Effects.HasEffect(player_id, _buff_skill_id))

	if not has_target_buff:
		_handled_current_buff = False
		return

	if _handled_current_buff or not _DIALOG_COOLDOWN_TIMER.IsExpired():
		return

	max_id = _find_nearby_max()
	if max_id <= 0:
		return

	_handled_current_buff = True
	_interaction_tree = _build_interaction_tree(max_id)


if __name__ == "__main__":
	main()
