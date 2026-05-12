"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Keep helper/internal methods out of the public discovery surface.

Routine docstring template
--------------------------
Each user-facing routine method should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: beginner
      Display: Move And Target
      Purpose: Build a tree that combines movement and a targeting step.
      UserDescription: Use this when you want to move first and then target something.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

from collections.abc import Callable
import random
from typing import Any, TYPE_CHECKING, Callable, TypedDict, cast

from ...Agent import Agent
from ...Map import Map
from ...enums_src.GameData_enums import Range
from ...native_src.internals.types import Point2D
from ...native_src.internals.types import PointPath
from ...native_src.internals.types import PointOrPath
from ...native_src.internals.types import Vec2f
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from .composite import BTComposite
from .composite import BTCompositeHelpers
from ...Player import Player
from ...GlobalCache import GLOBAL_CACHE
from ...enums import SharedCommandType
from ...py4gwcorelib_src.Console import ConsoleLog, Console
from ..Checks import Checks
from ...UIManager import UIManager
from ...enums_src.UI_enums import ControlAction



def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


DEFAULT_MOVE_TOLERANCE = 150.0

class BTMovement:
    """
    Public BT helper group for movement-first composite routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Movement
      Purpose: Group public BT routines that combine movement with targeting, interaction, and dialog flows.
      UserDescription: Built-in BT helper group for movement-driven BT routines.
      Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
    """
    @staticmethod
    def _as_path(pos: PointOrPath) -> list[Vec2f]:
        return PointPath.as_path(pos)

    @staticmethod
    def _build_path_tree(
        name: str,
        pos: PointOrPath,
        leaf_builder: Callable[[Vec2f], BehaviorTree],
    ) -> BehaviorTree:
        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(
                BehaviorTree.SucceederNode(
                    name=f"{name}EmptyPath",
                )
            )
        if len(points) == 1:
            return leaf_builder(points[0])
        return BTComposite.Sequence(
            *(leaf_builder(point) for point in points),
            name=name,
        )
        
    class _TimeoutState(TypedDict):
        started_ms: int | None
        waypoint_index: int | None
        paused_since_ms: int | None
        paused_total_ms: int

    class _MoveState(TypedDict):
        path_gen: Any | None
        path_points: list[Point2D] | None
        path_index: int
        last_distance: float | None
        last_progress_ms: int | None
        move_issued: bool
        completed: bool
        result_state: str
        result_reason: str
        initial_map_id: int | None
        last_move_point: Point2D | None
        pause_logged: bool
        was_paused: bool
        resume_recovery_active: bool
        resume_recovery_reason: str
        resume_recovery_restart_pending: bool
        current_pause_reason: str
        last_logged_waypoint_index: int
        failure_details: dict[str, Any]
        stall_retry_count: int
        strafe_side: str
        strafe_phase: int
        strafe_active: bool
        strafe_started_ms: int | None
        strafe_duration_ms: int
        last_move_command_ms: int | None
        
    #region Move
    @staticmethod
    def Move(
        x: float,
        y: float,
        tolerance: float = 50.0,
        timeout_ms: int = 15000,
        stall_threshold_ms: int = 500,
        pause_on_combat: bool = True,
        pause_flag_key: str = "PAUSE_MOVEMENT",
        log: bool = False,
        path_points_override: list[tuple[float, float]] | None = None,
    ) -> BehaviorTree:
        """
        Build a tree that moves the player to target coordinates using autopathing and runtime recovery logic.

        Meta:
            Expose: true
            Audience: advanced
            Display: Move
            Purpose: Move the player to target coordinates with waypoint tracking, pause handling, and timeout protection.
            UserDescription: Use this when you want a robust movement routine that can pause, recover, and report progress through the blackboard.
            Notes: Writes movement state to the blackboard and uses a parallel runtime with move, timeout, and map-transition watchers.
        """
        state: BTMovement._MoveState = {
            "path_gen": None,
            "path_points": None,
            "path_index": 0,
            "last_distance": None,
            "last_progress_ms": None,
            "move_issued": False,
            "completed": False,
            "result_state": "",
            "result_reason": "",
            "initial_map_id": None,
            "last_move_point": None,
            "pause_logged": False,
            "was_paused": False,
            "resume_recovery_active": False,
            "resume_recovery_reason": "",
            "resume_recovery_restart_pending": False,
            "current_pause_reason": "",
            "last_logged_waypoint_index": -1,
            "failure_details": {},
            "stall_retry_count": 0,
            "strafe_side": "",
            "strafe_phase": 0,
            "strafe_active": False,
            "strafe_started_ms": None,
            "strafe_duration_ms": 500,
            "last_move_command_ms": None,
        }

        def _reset_runtime() -> None:
            """
            Reset transient runtime movement state.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Reset Runtime Helper
                Purpose: Clear path-following and pause-related runtime state for the movement routine.
                UserDescription: Internal support routine.
                Notes: Leaves final result state alone so completion reporting can happen separately.
            """
            state["path_gen"] = None
            state["path_points"] = None
            state["path_index"] = 0
            state["last_distance"] = None
            state["last_progress_ms"] = None
            state["move_issued"] = False
            state["initial_map_id"] = None
            state["last_move_point"] = None
            state["pause_logged"] = False
            state["was_paused"] = False
            state["resume_recovery_active"] = False
            state["resume_recovery_reason"] = ""
            state["resume_recovery_restart_pending"] = False
            state["current_pause_reason"] = ""
            state["last_logged_waypoint_index"] = -1
            state["failure_details"] = {}
            state["stall_retry_count"] = 0
            state["strafe_side"] = ""
            state["strafe_phase"] = 0
            state["strafe_active"] = False
            state["strafe_started_ms"] = None
            state["strafe_duration_ms"] = 500
            state["last_move_command_ms"] = None

        def _reset_result() -> None:
            """
            Reset completion and failure-result tracking for movement.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Reset Result Helper
                Purpose: Clear the final result bookkeeping before a new movement attempt begins.
                UserDescription: Internal support routine.
                Notes: Preserves path runtime state until the broader runtime reset runs.
            """
            state["completed"] = False
            state["result_state"] = ""
            state["result_reason"] = ""
            state["failure_details"] = {}

        def _set_blackboard(node: BehaviorTree.Node, move_state: str, reason: str = "") -> None:
            """
            Publish movement state and path details to the blackboard.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Set Blackboard Helper
                Purpose: Write the current movement status, path information, and recovery flags to the blackboard.
                UserDescription: Internal support routine.
                Notes: Updates move-state keys consumed by diagnostics, UI, and downstream BT logic.
            """
            path_points: list[Point2D] = [
                (float(path_x), float(path_y))
                for path_x, path_y in (state["path_points"] or [])
            ]
            current_waypoint: Point2D | None = None
            current_waypoint_index: int = -1
            if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                waypoint_x, waypoint_y = state["path_points"][state["path_index"]]
                current_waypoint = (float(waypoint_x), float(waypoint_y))
                current_waypoint_index = int(state["path_index"])

            node.blackboard["move_state"] = move_state
            node.blackboard["move_reason"] = reason
            node.blackboard["move_target"] = (x, y)
            total_points: int = len(path_points)
            node.blackboard["move_path_index"] = int(state["path_index"])
            node.blackboard["move_path_count"] = int(total_points)
            node.blackboard["move_path_points"] = path_points
            node.blackboard["move_current_waypoint"] = current_waypoint
            node.blackboard["move_current_waypoint_index"] = current_waypoint_index
            node.blackboard["move_last_move_point"] = state["last_move_point"]
            node.blackboard["move_resume_recovery_active"] = bool(state["resume_recovery_active"])
            node.blackboard["move_resume_recovery_reason"] = state["resume_recovery_reason"]
            node.blackboard["move_resume_recovery_restart_pending"] = bool(state["resume_recovery_restart_pending"])
            node.blackboard["move_current_pause_reason"] = state["current_pause_reason"]
            node.blackboard["move_stall_retry_count"] = int(state["stall_retry_count"])
            node.blackboard["move_strafe_side"] = state["strafe_side"]
            node.blackboard["move_strafe_phase"] = int(state["strafe_phase"])
            node.blackboard["move_strafe_active"] = bool(state["strafe_active"])

        def _debug_enabled(node: BehaviorTree.Node) -> bool:
            """
            Determine whether verbose movement debug logging should be active.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Debug Enabled Helper
                Purpose: Use the routine log flag to control movement debug logging.
                UserDescription: Internal support routine.
                Notes: BT.Move should only emit verbose movement logs when the caller explicitly enables logging.
            """
            return log

        def _finalize_move(node: BehaviorTree.Node, move_state: str, reason: str = "") -> None:
            """
            Finalize movement with a terminal status and publish the result.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Finalize Move Helper
                Purpose: Mark movement complete, emit final diagnostics, publish blackboard state, and reset runtime state.
                UserDescription: Internal support routine.
                Notes: Includes detailed failure diagnostics when the movement result is `failed`.
            """
            state["completed"] = True
            state["result_state"] = move_state
            state["result_reason"] = reason
            _stop_strafe()
            if move_state == "failed":
                current_pos: Point2D = Player.GetXY()
                waypoint: Point2D | None = None
                distance_to_waypoint: float | None = None
                remaining_waypoints: int = 0
                if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                    waypoint = state["path_points"][state["path_index"]]
                    from ...Py4GWcorelib import Utils
                    distance_to_waypoint = Utils.Distance(current_pos, waypoint)
                    remaining_waypoints = len(state["path_points"]) - state["path_index"]
                failure_details: dict[str, Any] = state.get("failure_details", {})
                _fail_log(
                    "Move",
                    (
                        f"Movement failed: reason={reason or 'unknown'}, target=({x}, {y}), "
                        f"path_index={state['path_index']}, current_pos={current_pos}, "
                        f"waypoint={waypoint}, distance_to_waypoint={distance_to_waypoint}, "
                        f"remaining_waypoints={remaining_waypoints}, move_issued={state['move_issued']}, "
                        f"resume_recovery_active={state['resume_recovery_active']}, "
                        f"resume_recovery_reason={state['resume_recovery_reason']}, "
                        f"current_pause_reason={state['current_pause_reason']}, "
                        f"failure_details={failure_details}."
                    ),
                )
            elif _debug_enabled(node):
                _log(
                    "Move",
                    f"Finalizing move with state={move_state}, reason={reason or 'none'}, path_index={state['path_index']}.",
                    message_type=Console.MessageType.Info if move_state == "finished" else Console.MessageType.Warning,
                    log=True,
                )
            _set_blackboard(node, move_state, reason)
            _reset_runtime()

        def _get_pause_reason(node: BehaviorTree.Node) -> str:
            """
            Determine whether movement should pause and why.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Get Pause Reason Helper
                Purpose: Evaluate movement pause conditions such as loot handling, death, combat, external pause flags, and casting.
                UserDescription: Internal support routine.
                Notes: Returns an empty string when movement should continue normally.
            """
            account_email: str = Player.GetAccountEmail()
            index: int
            message: Any
            index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
            if (
                index != -1
                and message
                and message.Command == SharedCommandType.PickUpLoot
                and bool(getattr(message, "Running", False))
            ):
                return "loot_message_active"
            if Checks.Player.IsDead():
                return "player_dead"
            if pause_on_combat and bool(node.blackboard.get("COMBAT_ACTIVE", False)):
                return "combat"
            if bool(node.blackboard.get(pause_flag_key, False)):
                return "external_pause"
            if Checks.Player.IsCasting():
                return "casting"
            return ""

        def _issue_move(target_x: float, target_y: float) -> None:
            """
            Send a move command toward the current waypoint.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Issue Move Helper
                Purpose: Dispatch the low-level move command and apply small jitter when repeated move points are too similar.
                UserDescription: Internal support routine.
                Notes: Records the last issued move point so repeated nudges can avoid exact duplicates.
            """
            move_x: float = target_x
            move_y: float = target_y
            last_move_point: Point2D | None = state["last_move_point"]
            if last_move_point is not None:
                last_x, last_y = last_move_point
                if abs(move_x - last_x) <= 10 and abs(move_y - last_y) <= 10:
                    move_x += random.uniform(-10.0, 10.0)
                    move_y += random.uniform(-10.0, 10.0)
            Player.Move(move_x, move_y)
            state["last_move_point"] = (move_x, move_y)
            from ...Py4GWcorelib import Utils
            state["last_move_command_ms"] = Utils.GetBaseTimestamp()
            if log:
                if move_x != target_x or move_y != target_y:
                    _log(
                        "Move",
                        f"Moving to waypoint ({target_x}, {target_y}) with jittered point ({move_x}, {move_y}).",
                        message_type=Console.MessageType.Info,
                        log=log,
                    )
                else:
                    _log("Move", f"Moving to waypoint ({target_x}, {target_y}).", message_type=Console.MessageType.Info, log=log)

        def _get_combat_move_issue_cooldown_ms() -> int:
            player_living = Agent.GetLivingAgentByID(Player.GetAgentID())
            if player_living is None:
                return 1750

            attack_speed = float(getattr(player_living, "weapon_attack_speed", 0.0) or 0.0)
            attack_speed_modifier = float(getattr(player_living, "attack_speed_modifier", 1.0) or 1.0)
            if attack_speed <= 0.0:
                attack_speed = 1.75
            if attack_speed_modifier <= 0.0:
                attack_speed_modifier = 1.0
            return max(250, int((attack_speed / attack_speed_modifier) * 1000))

        def _try_issue_move(node: BehaviorTree.Node, target_x: float, target_y: float, now: int) -> bool:
            if bool(node.blackboard.get("COMBAT_ACTIVE", False)) and not pause_on_combat:
                last_move_command_ms = state["last_move_command_ms"]
                if last_move_command_ms is not None:
                    cooldown_ms = _get_combat_move_issue_cooldown_ms()
                    elapsed_ms = now - last_move_command_ms
                    if elapsed_ms < cooldown_ms:
                        _set_blackboard(node, "running", "waiting_attack_window")
                        return False

            _issue_move(target_x, target_y)
            return True

        def _stop_strafe() -> None:
            if not state["strafe_active"]:
                return

            if state["strafe_side"] == "left":
                UIManager.Keyup(ControlAction.ControlAction_StrafeLeft.value, 0)
            elif state["strafe_side"] == "right":
                UIManager.Keyup(ControlAction.ControlAction_StrafeRight.value, 0)

            state["strafe_active"] = False
            state["strafe_started_ms"] = None
            state["strafe_duration_ms"] = 500

        def _start_strafe(side: str, now: int) -> None:
            _stop_strafe()

            if side == "left":
                UIManager.Keydown(ControlAction.ControlAction_StrafeLeft.value, 0)
            else:
                UIManager.Keydown(ControlAction.ControlAction_StrafeRight.value, 0)

            state["strafe_side"] = side
            state["strafe_active"] = True
            state["strafe_started_ms"] = now
            state["strafe_duration_ms"] = random.randint(500, 1000)

        def _tick_strafe(now: int) -> bool:
            if not state["strafe_active"]:
                return False

            started_ms = state["strafe_started_ms"]
            if started_ms is None:
                _stop_strafe()
                return False

            if now - started_ms < state["strafe_duration_ms"]:
                return True

            _stop_strafe()
            return False

        def _move(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            """
            Drive the main movement execution loop.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Move Executor Helper
                Purpose: Resolve or consume path points, handle progress, pauses, retries, and completion for the movement routine.
                UserDescription: Internal support routine.
                Notes: Returns running while pathing continues, success on completion, and failure on unrecoverable movement errors.
            """
            from ...Pathing import AutoPathing
            from ...Py4GWcorelib import Utils

            now: int = Utils.GetBaseTimestamp()
            effective_tolerance: float = max(float(tolerance), 125.0) if not pause_on_combat else float(tolerance)
            if state["completed"] and state["result_state"] == "finished":
                if log:
                    _log("Move", f"Movement already finished ({state['result_reason']}).", message_type=Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            if state["completed"] and state["result_state"] == "failed":
                if log:
                    _log("Move", f"Movement already failed ({state['result_reason']}).", message_type=Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            if state["path_gen"] is None and state["path_points"] is None:
                _reset_result()
                state["initial_map_id"] = Map.GetMapID()
                if path_points_override is not None:
                    state["path_gen"] = None
                    state["path_points"] = [
                        (float(path_x), float(path_y))
                        for path_x, path_y in path_points_override
                    ]
                    state["path_index"] = 0
                    state["move_issued"] = False
                    state["last_distance"] = None
                    state["last_progress_ms"] = now
                    state["pause_logged"] = False
                    state["last_logged_waypoint_index"] = -1
                    if _debug_enabled(node):
                        _log(
                            "MoveDirect",
                            f"Starting direct move with {len(state['path_points'])} supplied points to ({x}, {y}).",
                            message_type=Console.MessageType.Info,
                            log=True,
                        )
                    _set_blackboard(node, "running")
                else:
                    state["path_gen"] = AutoPathing().get_path_to(x, y, margin=250)
                    if _debug_enabled(node):
                        _log("Move", f"Starting autopath to ({x}, {y}).", message_type=Console.MessageType.Info, log=True)
                    _set_blackboard(node, "running")

            if state["path_gen"] is not None:
                try:
                    next(state["path_gen"])
                    _set_blackboard(node, "running")
                    return BehaviorTree.NodeState.RUNNING
                except StopIteration as path_result:
                    state["path_points"] = list(path_result.value or [])
                    state["path_gen"] = None
                    state["path_index"] = 0
                    state["move_issued"] = False
                    state["last_distance"] = None
                    state["last_progress_ms"] = now
                    state["pause_logged"] = False
                    state["last_logged_waypoint_index"] = -1

                    if _debug_enabled(node):
                        _log(
                            "Move",
                            f"Autopath resolved with {len(state['path_points'])} points to ({x}, {y}).",
                            message_type=Console.MessageType.Info,
                            log=True,
                        )

                    current_pos: Point2D = Player.GetXY()
                    if Utils.Distance(current_pos, (x, y)) <= effective_tolerance:
                        if _debug_enabled(node):
                            _log("Move", "Already within tolerance of destination.", message_type=Console.MessageType.Success, log=True)
                        _finalize_move(node, "finished")
                        return BehaviorTree.NodeState.SUCCESS

                    if len(state["path_points"]) == 0:
                        if _debug_enabled(node):
                            _fail_log("Move", "Autopath returned no path points; failing because there is no path to follow.")
                        _finalize_move(node, "failed", "autopath_failed")
                        return BehaviorTree.NodeState.FAILURE

            if Checks.Player.IsDead():
                _stop_strafe()
                if log:
                    _log("Move", "Player is dead; movement remains active and waiting.", message_type=Console.MessageType.Warning, log=log)
                state["was_paused"] = True
                state["current_pause_reason"] = "player_dead"
                state["last_progress_ms"] = None
                state["last_distance"] = None
                state["move_issued"] = False
                state["last_move_point"] = None
                state["resume_recovery_active"] = False
                state["resume_recovery_reason"] = ""
                state["stall_retry_count"] = 0
                state["strafe_side"] = ""
                state["strafe_phase"] = 0
                _set_blackboard(node, "paused", "player_dead")
                return BehaviorTree.NodeState.RUNNING

            pause_reason: str = _get_pause_reason(node)
            if pause_reason:
                _stop_strafe()
                if not state["pause_logged"] and log:
                        _log("Move", f"Movement paused due to {pause_reason}.", message_type=Console.MessageType.Info, log=log)
                state["pause_logged"] = True
                state["was_paused"] = True
                state["current_pause_reason"] = pause_reason
                state["last_progress_ms"] = None
                state["last_distance"] = None
                state["move_issued"] = False
                state["last_move_point"] = None
                state["resume_recovery_active"] = False
                state["resume_recovery_reason"] = ""
                state["stall_retry_count"] = 0
                state["strafe_side"] = ""
                state["strafe_phase"] = 0
                _set_blackboard(node, "paused", pause_reason)
                return BehaviorTree.NodeState.RUNNING
            elif state["pause_logged"]:
                if log:
                    _log("Move", "Movement resumed.", message_type=Console.MessageType.Info, log=log)
                state["pause_logged"] = False
            if state["was_paused"]:
                state["was_paused"] = False
                state["resume_recovery_active"] = True
                state["resume_recovery_reason"] = state["current_pause_reason"]
                state["resume_recovery_restart_pending"] = True
                state["current_pause_reason"] = ""
                state["move_issued"] = False
                state["last_distance"] = None
                state["last_progress_ms"] = now
                state["last_move_point"] = None

            if state["path_points"] is None or state["path_index"] >= len(state["path_points"]):
                if log:
                    _log("Move", "Movement finished with no remaining path points.", message_type=Console.MessageType.Success, log=log)
                _finalize_move(node, "finished")
                return BehaviorTree.NodeState.SUCCESS

            target_x, target_y = state["path_points"][state["path_index"]]
            if state["last_logged_waypoint_index"] != state["path_index"] and log:
                _log(
                    "Move",
                    f"Tracking waypoint {state['path_index'] + 1}/{len(state['path_points'])} at ({target_x}, {target_y}).",
                    message_type=Console.MessageType.Info,
                    log=log,
                )
                state["last_logged_waypoint_index"] = state["path_index"]
            current_pos: Point2D = Player.GetXY()
            current_distance: float = Utils.Distance(current_pos, (target_x, target_y))

            if pause_on_combat and _tick_strafe(now):
                _set_blackboard(node, "running", f"strafing_{state['strafe_side']}")
                return BehaviorTree.NodeState.RUNNING

            if current_distance <= effective_tolerance:
                _stop_strafe()
                state["path_index"] += 1
                state["move_issued"] = False
                state["last_distance"] = None
                state["last_progress_ms"] = now
                state["resume_recovery_active"] = False
                state["resume_recovery_reason"] = ""
                state["resume_recovery_restart_pending"] = True
                state["stall_retry_count"] = 0
                state["strafe_side"] = ""
                state["strafe_phase"] = 0
                if log:
                    _log("Move", f"Reached waypoint, advancing to index {state['path_index']}.", message_type=Console.MessageType.Info, log=log)

                if state["path_index"] >= len(state["path_points"]):
                    if log:
                        _log("Move", "Reached final destination.", message_type=Console.MessageType.Success, log=log)
                    _finalize_move(node, "finished")
                    return BehaviorTree.NodeState.SUCCESS

                target_x, target_y = state["path_points"][state["path_index"]]
                if not _try_issue_move(node, target_x, target_y, now):
                    return BehaviorTree.NodeState.RUNNING
                state["move_issued"] = True
                state["last_distance"] = Utils.Distance(Player.GetXY(), (target_x, target_y))
                state["last_progress_ms"] = now
                _set_blackboard(node, "running")
                return BehaviorTree.NodeState.RUNNING

            if not state["move_issued"]:
                _stop_strafe()
                if not _try_issue_move(node, target_x, target_y, now):
                    return BehaviorTree.NodeState.RUNNING
                state["move_issued"] = True
                state["last_distance"] = current_distance
                state["last_progress_ms"] = now
                _set_blackboard(node, "running")
                return BehaviorTree.NodeState.RUNNING

            if state["last_distance"] is None or current_distance < state["last_distance"] - 1.0:
                _stop_strafe()
                state["last_distance"] = current_distance
                state["last_progress_ms"] = now
                state["stall_retry_count"] = 0
            elif state["last_progress_ms"] is not None and now - state["last_progress_ms"] >= stall_threshold_ms:
                state["stall_retry_count"] += 1
                if log:
                    _log(
                        "Move",
                        f"No progress for {stall_threshold_ms}ms, nudging waypoint ({target_x}, {target_y}); retry {state['stall_retry_count']}.",
                        message_type=Console.MessageType.Warning,
                        log=log,
                    )
                if pause_on_combat and state["stall_retry_count"] >= 4:
                    if state["strafe_phase"] == 0:
                        chosen_side = random.choice(("left", "right"))
                        state["strafe_phase"] = 1
                        _start_strafe(chosen_side, now)
                        if log:
                            _log(
                                "Move",
                                f"Retry threshold reached; strafing {chosen_side} for {state['strafe_duration_ms']}ms before reattempting movement.",
                                message_type=Console.MessageType.Warning,
                                log=log,
                            )
                        state["stall_retry_count"] = 0
                        state["last_progress_ms"] = now
                        _set_blackboard(node, "running", f"strafing_{chosen_side}")
                        return BehaviorTree.NodeState.RUNNING
                    if state["strafe_phase"] == 1:
                        opposite_side = "right" if state["strafe_side"] == "left" else "left"
                        state["strafe_phase"] = 2
                        _start_strafe(opposite_side, now)
                        if log:
                            _log(
                                "Move",
                                f"Still stalled after post-strafe retries; strafing {opposite_side} for {state['strafe_duration_ms']}ms.",
                                message_type=Console.MessageType.Warning,
                                log=log,
                            )
                        state["stall_retry_count"] = 0
                        state["last_progress_ms"] = now
                        _set_blackboard(node, "running", f"strafing_{opposite_side}")
                        return BehaviorTree.NodeState.RUNNING
                if not _try_issue_move(node, target_x, target_y, now):
                    return BehaviorTree.NodeState.RUNNING
                state["last_progress_ms"] = now
                state["last_distance"] = current_distance

            _set_blackboard(node, "running")
            return BehaviorTree.NodeState.RUNNING

        timeout_state: BTMovement._TimeoutState = {
            "started_ms": None,
            "waypoint_index": None,
            "paused_since_ms": None,
            "paused_total_ms": 0,
        }

        def _reset_timeout() -> None:
            """
            Reset timeout watcher state for the current waypoint.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Reset Timeout Helper
                Purpose: Clear timeout-tracking timestamps and waypoint bookkeeping for the movement timeout watcher.
                UserDescription: Internal support routine.
                Notes: Called when movement pauses, finishes, fails, or restarts from a new waypoint.
            """
            timeout_state["started_ms"] = None
            timeout_state["waypoint_index"] = None
            timeout_state["paused_since_ms"] = None
            timeout_state["paused_total_ms"] = 0

        def _timeout(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            """
            Watch the active waypoint for movement timeout conditions.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Timeout Helper
                Purpose: Fail the movement routine when waypoint progress exceeds the configured timeout budget.
                UserDescription: Internal support routine.
                Notes: Extends the timeout budget during resume recovery and ignores time spent while movement is paused.
            """
            from ...Py4GWcorelib import Utils

            if state["completed"] and state["result_state"] == "finished":
                if log:
                    _log("Move", f"Timeout watcher finished because movement succeeded ({state['result_reason']}).", message_type=Console.MessageType.Info, log=log)
                _reset_timeout()
                return BehaviorTree.NodeState.SUCCESS

            if state["completed"] and state["result_state"] == "failed":
                if log:
                    _log("Move", f"Timeout watcher finished because movement failed: {state['result_reason']}.", message_type=Console.MessageType.Info, log=log)
                _reset_timeout()
                return BehaviorTree.NodeState.SUCCESS

            if not pause_on_combat:
                _reset_timeout()
                return BehaviorTree.NodeState.RUNNING

            pause_reason: str = _get_pause_reason(node)
            is_paused: bool = bool(pause_reason)

            now: int = Utils.GetBaseTimestamp()

            if is_paused:
                _reset_timeout()
                return BehaviorTree.NodeState.RUNNING

            if state["path_points"] is None or state["path_index"] >= len(state["path_points"]):
                return BehaviorTree.NodeState.RUNNING

            if timeout_state["waypoint_index"] != state["path_index"]:
                timeout_state["started_ms"] = now
                timeout_state["waypoint_index"] = state["path_index"]
                timeout_state["paused_since_ms"] = None
                timeout_state["paused_total_ms"] = 0
                return BehaviorTree.NodeState.RUNNING

            if timeout_state["started_ms"] is None:
                timeout_state["started_ms"] = now
                timeout_state["waypoint_index"] = state["path_index"]
                return BehaviorTree.NodeState.RUNNING

            if state["resume_recovery_restart_pending"]:
                timeout_state["started_ms"] = now
                timeout_state["waypoint_index"] = state["path_index"]
                timeout_state["paused_since_ms"] = None
                timeout_state["paused_total_ms"] = 0
                state["resume_recovery_restart_pending"] = False
                return BehaviorTree.NodeState.RUNNING

            RECOVERY_FACTOR: int = 3
            elapsed_ms: int = now - cast(int, timeout_state["started_ms"]) - timeout_state["paused_total_ms"]
            effective_timeout_ms: int = timeout_ms * RECOVERY_FACTOR if state["resume_recovery_active"] else timeout_ms
            if effective_timeout_ms > 0 and elapsed_ms >= effective_timeout_ms:
                current_pos: Point2D = Player.GetXY()
                waypoint: Point2D | None = None
                distance_to_waypoint: float | None = None
                if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                    waypoint = state["path_points"][state["path_index"]]
                    distance_to_waypoint = Utils.Distance(current_pos, waypoint)
                state["failure_details"] = {
                    "timeout_elapsed_ms": int(elapsed_ms),
                    "timeout_budget_ms": int(effective_timeout_ms),
                    "base_timeout_ms": int(timeout_ms),
                    "paused_total_ms": int(timeout_state["paused_total_ms"]),
                    "paused_since_ms": timeout_state["paused_since_ms"],
                    "resume_recovery_active": bool(state["resume_recovery_active"]),
                    "resume_recovery_reason": state["resume_recovery_reason"],
                    "current_pause_reason": state["current_pause_reason"],
                    "current_pos": current_pos,
                    "current_waypoint": waypoint,
                    "distance_to_waypoint": distance_to_waypoint,
                }
                _fail_log(
                    "Move",
                    (
                        f"Movement timed out after {elapsed_ms}ms on path_index={state['path_index']} "
                        f"(budget={effective_timeout_ms}ms, base_timeout={timeout_ms}ms, "
                        f"paused_total={timeout_state['paused_total_ms']}ms, "
                        f"resume_recovery_active={state['resume_recovery_active']}, "
                        f"resume_recovery_reason='{state['resume_recovery_reason']}', "
                        f"current_pause_reason='{state['current_pause_reason']}', "
                        f"current_pos={current_pos}, "
                        f"waypoint={waypoint}, distance_to_waypoint={distance_to_waypoint})."
                    ),
                )
                _finalize_move(node, "failed", "timeout")
                _reset_timeout()
                return BehaviorTree.NodeState.FAILURE

            return BehaviorTree.NodeState.RUNNING

        def _map_transition(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            """
            Detect successful completion through map loading or map change.

            Meta:
                Expose: false
                Audience: advanced
                Display: Internal Map Transition Helper
                Purpose: Finish the movement routine when map loading begins or the map id changes after movement starts.
                UserDescription: Internal support routine.
                Notes: Treats temporary map invalidity as a wait condition rather than an immediate failure.
            """
            if state["completed"] and state["result_state"] == "finished":
                return BehaviorTree.NodeState.SUCCESS

            if state["completed"] and state["result_state"] == "failed":
                return BehaviorTree.NodeState.SUCCESS

            current_map_id: int = Map.GetMapID()
            initial_map_id: int = int(state["initial_map_id"] or 0)
            map_loading: bool = Map.IsMapLoading()
            map_changed: bool = (
                initial_map_id != 0
                and current_map_id != 0
                and current_map_id != initial_map_id
            )

            if map_loading or map_changed:
                reason = "map_loading" if map_loading else "map_changed"
                if _debug_enabled(node):
                    _log(
                        "Move",
                        f"Movement finished successfully due to {reason}.",
                        message_type=Console.MessageType.Info,
                        log=True,
                    )
                _finalize_move(node, "finished", reason)
                return BehaviorTree.NodeState.SUCCESS

            if not Checks.Map.MapValid():
                if _debug_enabled(node):
                    _log(
                        "Move",
                        "Map is temporarily invalid during movement; waiting without finalizing move.",
                        message_type=Console.MessageType.Info,
                        log=True,
                    )
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree.NodeState.RUNNING

        move_node = BehaviorTree.ConditionNode(
            name="MoveExecutor",
            condition_fn=lambda node: _move(node),
        )
        timeout_node = BehaviorTree.ConditionNode(
            name="MoveTimeout",
            condition_fn=lambda node: _timeout(node),
        )
        map_transition_node = BehaviorTree.ConditionNode(
            name="MoveMapTransition",
            condition_fn=lambda node: _map_transition(node),
        )
        class _MoveParallelNode(BehaviorTree.ParallelNode):
            def reset(self) -> None:
                super().reset()
                _reset_runtime()
                _reset_result()
                _reset_timeout()

        tree: _MoveParallelNode = _MoveParallelNode(
            name="Move",
            children=[move_node, timeout_node, map_transition_node],
        )
        return BehaviorTree(tree)

    @staticmethod
    def MoveDirect(
        path_points: list[Vec2f],
        tolerance: float = 50.0,
        timeout_ms: int = 15000,
        stall_threshold_ms: int = 500,
        pause_on_combat: bool = True,
        pause_flag_key: str = "PAUSE_MOVEMENT",
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that follows caller-supplied waypoints using the same movement runtime as `Move`.

        Meta:
            Expose: true
            Audience: advanced
            Display: Move Direct
            Purpose: Follow a supplied waypoint list using the same movement runtime as `Move`.
            UserDescription: Use this when you already have a path and want the BT mover to follow it directly.
            Notes: Fails immediately on an empty waypoint list and otherwise forwards to `Move` with `path_points_override`.
        """
        if not path_points:
            return BehaviorTree(
                BehaviorTree.FailerNode(
                    name="MoveDirectEmptyPath",
                )
            )

        final_x, final_y = path_points[-1].x, path_points[-1].y
        return BTMovement.Move(
            x=float(final_x),
            y=float(final_y),
            tolerance=tolerance,
            timeout_ms=timeout_ms,
            stall_threshold_ms=stall_threshold_ms,
            pause_on_combat=pause_on_combat,
            pause_flag_key=pause_flag_key,
            log=log,
            path_points_override=[
                (float(path_point.x), float(path_point.y))
                for path_point in path_points
            ],
        )
        
    @staticmethod
    def MoveAndKill(
        coords: Vec2f,
        clear_area_radius: float = Range.Spirit.value,
        pause_on_combat: bool = True,
    ) -> BehaviorTree:
        from .agents import BTAgents

        return BTComposite.Sequence(
            BTMovement.Move(x=coords.x, y=coords.y, pause_on_combat=pause_on_combat),
            BTAgents.ClearEnemiesInArea(x=coords.x, y=coords.y, radius=clear_area_radius),
            name="MoveAndKill",
        )

        

    @staticmethod
    def _move_to_model_id(
        modelID_or_encStr: int | str,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build an internal support tree that resolves an agent by model id and moves to its coordinates.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Move To Model ID Helper
          Purpose: Resolve an agent by model id and compose the movement subtree used by public movement routines.
          UserDescription: Internal support routine.
          Notes: Stores the resolved agent id and coordinates on the blackboard before delegating to `BTPlayer.Move`.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        def _move_to_resolved_agent(node: BehaviorTree.Node):
            """
            Convert the resolved model-id lookup result into a concrete move subtree.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Move To Resolved Agent Helper
              Purpose: Read the resolved agent id from the blackboard, store coordinates, and build the move subtree.
              UserDescription: Internal support routine.
              Notes: Returns a failing tree when no agent id has been resolved yet.
            """
            agent_id = int(node.blackboard.get("result", 0) or 0)
            if agent_id == 0:
                return BehaviorTree(BehaviorTree.FailerNode(name="MoveToModelIDMissingAgent"))

            agent_x, agent_y = Agent.GetXY(agent_id)
            node.blackboard["resolved_agent_id"] = agent_id
            node.blackboard["resolved_agent_xy"] = (agent_x, agent_y)
            return BTMovement.Move(
                x=agent_x,
                y=agent_y,
                tolerance=Range.Adjacent.value,
                pause_on_combat=pause_on_combat,
                log=log,
            )

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToModelID",
                children=[
                    BehaviorTree.SubtreeNode(
                        name="GetAgentIDByModelIDSubtree",
                        subtree_fn=lambda node: BTAgents.GetAgentIDByModelID(modelID_or_encStr, log=log),
                    ),
                    BehaviorTree.SubtreeNode(
                        name="MoveToResolvedAgentXYSubtree",
                        subtree_fn=_move_to_resolved_agent,
                    ),
                ],
            )
        )

    @staticmethod
    def MoveAndTarget(
        x: float,
        y: float,
        target_distance: float = Range.Adjacent.value,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates and then targets the nearest NPC.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move And Target
          Purpose: Move to a location and then target a nearby NPC.
          UserDescription: Use this when you want to walk somewhere first and then acquire a nearby NPC target.
          Notes: Combines the player move routine with the nearest-NPC targeting routine.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_and_target(
            move_tree=BTMovement.Move(x=x, y=y, pause_on_combat=pause_on_combat, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
        )

    @staticmethod
    def MovePath(
        pos: PointOrPath,
        pause_on_combat: bool = True,
        tolerance: float = DEFAULT_MOVE_TOLERANCE,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path of one or more points.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move Path
          Purpose: Move through a path of world coordinates in order.
          UserDescription: Use this when you want to walk through multiple points instead of a single destination.
          Notes: A single point collapses to one move step; an empty path succeeds immediately.
        """
        from .player import BTPlayer

        return BTMovement._build_path_tree(
            "MovePath",
            pos,
            lambda point: BTMovement.Move(
                x=point.x,
                y=point.y,
                tolerance=tolerance,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
        )

    @staticmethod
    def MoveTargetAndInteract(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates, targets a nearby NPC, and interacts.

        Meta:
          Expose: true
          Audience: beginner
          Display: Move Target And Interact
          Purpose: Move to a location, target a nearby NPC, and interact with it.
          UserDescription: Use this when you want to travel to an area and immediately interact with a nearby NPC.
          Notes: Uses the nearest-NPC target search after movement before calling player interaction.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_target_and_interact(
            move_tree=BTMovement.Move(x=x, y=y, pause_on_combat=pause_on_combat, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            log=log,
        )

    @staticmethod
    def MoveAndKillPath(
        pos: PointOrPath,
        clear_area_radius: float = Range.Spirit.value,
        pause_on_combat: bool = True,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path and clears enemies around each point.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Kill Path
          Purpose: Walk through path points and clear enemies around each point.
          UserDescription: Use this when a route should advance point by point while clearing nearby enemies.
          Notes: A single point collapses to the existing move-and-kill routine.
        """
        from .player import BTPlayer

        return BTMovement._build_path_tree(
            "MoveAndKillPath",
            pos,
            lambda point: BTMovement.MoveAndKill(
                coords=point,
                clear_area_radius=clear_area_radius,
                pause_on_combat=pause_on_combat,
            ),
        )

    @staticmethod
    def MoveAndTargetPath(
        pos: PointOrPath,
        target_distance: float = Range.Adjacent.value,
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path and targets the nearest NPC at the final point.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Target Path
          Purpose: Walk through path points and then target a nearby NPC at the final point.
          UserDescription: Use this when you want multi-point movement before targeting an NPC near the destination.
          Notes: Intermediate points only move; targeting happens at the final point.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(BehaviorTree.SucceederNode(name="MoveAndTargetPathEmptyPath"))
        final_point = points[-1]
        return BTComposite.Sequence(
            *[
                BTMovement.Move(
                    x=point.x,
                    y=point.y,
                    tolerance=move_tolerance,
                    pause_on_combat=pause_on_combat,
                    log=False,
                )
                for point in points
            ],
            BTAgents.TargetNearestNPCXY(
                x=final_point.x,
                y=final_point.y,
                distance=target_distance,
                log=log,
            ),
            name="MoveAndTargetPath",
        )

    @staticmethod
    def MoveAndTargetGadgetPath(
        pos: PointOrPath,
        target_distance: float = Range.Adjacent.value,
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path and targets the nearest gadget at the final point.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Target Gadget Path
          Purpose: Walk through path points and then target a nearby gadget at the final point.
          UserDescription: Use this when you want multi-point movement before targeting a gadget near the destination.
          Notes: Intermediate points only move; gadget targeting happens at the final point.
        """
        from .agents import BTAgents

        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(BehaviorTree.SucceederNode(name="MoveAndTargetGadgetPathEmptyPath"))
        final_point = points[-1]
        return BTComposite.Sequence(
            *[
                BTMovement.Move(
                    x=point.x,
                    y=point.y,
                    tolerance=move_tolerance,
                    pause_on_combat=pause_on_combat,
                    log=False,
                )
                for point in points
            ],
            BTAgents.TargetNearestGadgetXY(
                x=final_point.x,
                y=final_point.y,
                distance=target_distance,
                log=log,
            ),
            name="MoveAndTargetGadgetPath",
        )

    @staticmethod
    def MoveTargetAndInteractPath(
        pos: PointOrPath,
        target_distance: float = Range.Area.value,
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path, targets a nearby NPC at the final point, and interacts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target And Interact Path
          Purpose: Walk through path points and then target and interact with a nearby NPC at the destination.
          UserDescription: Use this when an NPC interaction requires moving through multiple points first.
          Notes: Intermediate points only move; targeting and interaction happen at the final point.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(BehaviorTree.SucceederNode(name="MoveTargetAndInteractPathEmptyPath"))
        final_point = points[-1]
        return BTComposite.Sequence(
            *[
                BTMovement.Move(
                    x=point.x,
                    y=point.y,
                    tolerance=move_tolerance,
                    pause_on_combat=pause_on_combat,
                    log=False,
                )
                for point in points
            ],
            BTAgents.TargetNearestNPCXY(
                x=final_point.x,
                y=final_point.y,
                distance=target_distance,
                log=log,
            ),
            BTPlayer.InteractTarget(log=log),
            BTPlayer.Wait(250, log=False),
            name="MoveTargetAndInteractPath",
        )

    @staticmethod
    def MoveTargetInteractAndDialog(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        dialog_id: str | int = 0,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves, targets, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog
          Purpose: Move to a location, interact with a nearby NPC, and send a dialog id.
          UserDescription: Use this when an interaction flow needs both travel and a follow-up dialog selection.
          Notes: Sends a manual dialog id after the interaction succeeds.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers.move_target_interact_and_dialog(
            move_tree=BTMovement.Move(x=x, y=y, pause_on_combat=pause_on_combat, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            dialog_id=dialog_id,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndDialogPath(
        pos: PointOrPath,
        dialog_id: str | int,
        target_distance: float = Range.Nearby.value,
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path, targets a nearby NPC at the final point, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog Path
          Purpose: Walk through path points and then interact with a nearby NPC using a dialog id.
          UserDescription: Use this when an NPC dialog interaction needs multi-point movement first.
          Notes: Intermediate points only move; targeting, interaction, and dialog happen at the final point.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(BehaviorTree.SucceederNode(name="MoveTargetInteractAndDialogPathEmptyPath"))
        final_point = points[-1]
        return BTComposite.Sequence(
            *[
                BTMovement.Move(
                    x=point.x,
                    y=point.y,
                    tolerance=move_tolerance,
                    pause_on_combat=pause_on_combat,
                    log=False,
                )
                for point in points
            ],
            BTAgents.TargetNearestNPCXY(
                x=final_point.x,
                y=final_point.y,
                distance=target_distance,
                log=log,
            ),
            BTPlayer.InteractTarget(log=log),
            BTPlayer.Wait(250, log=False),
            BTPlayer.SendDialog(dialog_id=dialog_id, log=log),
            name="MoveTargetInteractAndDialogPath",
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialog(
        x: float,
        y: float,
        target_distance: float = Range.Nearby.value,
        button_number: int = 0,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves, targets, interacts, and sends an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog
          Purpose: Move to a location, interact with a nearby NPC, and press an automatic dialog button.
          UserDescription: Use this when an interaction flow requires choosing a visible dialog button after traveling.
          Notes: Waits for the dialog state and then sends the requested button index.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTCompositeHelpers._interact_and_automatic_dialog(
            move_tree=BTMovement.Move(x=x, y=y, pause_on_combat=pause_on_combat, log=log),
            target_tree=BTAgents.TargetNearestNPC(distance=target_distance, log=log),
            button_number=button_number,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialogPath(
        pos: PointOrPath,
        button_number: int = 0,
        target_distance: float = Range.Nearby.value,
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that walks a path, targets a nearby NPC at the final point, interacts, and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog Path
          Purpose: Walk through path points and then interact with a nearby NPC using an automatic dialog choice.
          UserDescription: Use this when a visible dialog button selection needs multi-point movement first.
          Notes: Intermediate points only move; targeting, interaction, and automatic dialog happen at the final point.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        points = BTMovement._as_path(pos)
        if not points:
            return BehaviorTree(BehaviorTree.SucceederNode(name="MoveTargetInteractAndAutomaticDialogPathEmptyPath"))
        final_point = points[-1]
        return BTComposite.Sequence(
            *[
                BTMovement.Move(
                    x=point.x,
                    y=point.y,
                    tolerance=move_tolerance,
                    pause_on_combat=pause_on_combat,
                    log=False,
                )
                for point in points
            ],
            BTAgents.TargetNearestNPCXY(
                x=final_point.x,
                y=final_point.y,
                distance=target_distance,
                log=log,
            ),
            BTPlayer.InteractTarget(log=log),
            BTPlayer.Wait(250, log=False),
            BTPlayer.SendAutomaticDialog(button_number=button_number, log=log),
            name="MoveTargetInteractAndAutomaticDialogPath",
        )

    @staticmethod
    def DialogAtXY(
        x: float,
        y: float,
        dialog_id: int | str,
        target_distance: float = 200.0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that targets the nearest NPC around coordinates, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Dialog At XY
          Purpose: Interact with the nearest NPC around coordinates and send a dialog id.
          UserDescription: Use this when you are already in place and only need to target, interact, and send dialog.
          Notes: This does not include movement.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTComposite.Sequence(
            BTAgents.TargetNearestNPCXY(x=x, y=y, distance=target_distance, log=log),
            BTPlayer.InteractTarget(log=log),
            BTPlayer.Wait(250, log=False),
            BTPlayer.SendDialog(dialog_id=dialog_id, log=log),
            name="DialogAtXY",
        )

    @staticmethod
    def InteractWithGadgetAtXY(
        x: float,
        y: float,
        target_distance: float = 200.0,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that targets the nearest gadget around coordinates and interacts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Interact With Gadget At XY
          Purpose: Interact with the nearest gadget around coordinates.
          UserDescription: Use this when you are already in place and only need to target and interact with a gadget.
          Notes: This does not include movement.
        """
        from .agents import BTAgents
        from .player import BTPlayer

        return BTComposite.Sequence(
            BTAgents.TargetNearestGadgetXY(x=x, y=y, distance=target_distance, log=log),
            BTPlayer.InteractTarget(log=log),
            BTPlayer.Wait(250, log=False),
            name="InteractWithGadgetAtXY",
        )

    @staticmethod
    def MoveAndExitMap(
        x: float,
        y: float,
        target_map_id: int = 0,
        target_map_name: str = "",
        move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that moves to coordinates and waits until the requested map loads.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Exit Map
          Purpose: Move to an exit point and wait for the target map to load.
          UserDescription: Use this when crossing a portal or zone line should transition into a known map.
          Notes: Accepts either a target map id or a target map name.
        """
        from .map import BTMap
        from .player import BTPlayer

        resolved_map_id = BTMap._resolve_map_id(target_map_id, target_map_name)
        return BTComposite.Sequence(
            BTMovement.Move(
                x=x,
                y=y,
                tolerance=move_tolerance,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
            BTMap.WaitforMapLoad(
                map_id=resolved_map_id,
            ),
            name="MoveAndExitMap",
        )

    @staticmethod
    def MoveAndTargetByModelID(
        modelID_or_encStr: int | str,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and targets it.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move And Target By Model ID
          Purpose: Resolve an agent by model id, move to its position, and target it.
          UserDescription: Use this when you know the model id of the agent you want to approach and target.
          Notes: Resolves the current agent id dynamically before movement and targeting.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_and_target(
            move_tree=BTMovement._move_to_model_id(
                modelID_or_encStr=modelID_or_encStr,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
        )

    @staticmethod
    def MoveTargetAndInteractByModelID(
        modelID_or_encStr: int | str,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, and interacts.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target And Interact By Model ID
          Purpose: Resolve an agent by model id, move to it, target it, and interact.
          UserDescription: Use this when you want a direct approach-and-interact flow for a known model id.
          Notes: Uses the shared model-id resolver before running the interaction sequence.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_target_and_interact(
            move_tree=BTMovement._move_to_model_id(
                modelID_or_encStr=modelID_or_encStr,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndDialogByModelID(
        modelID_or_encStr: int | str,
        dialog_id: str | int = 0,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and sends a dialog id.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Dialog By Model ID
          Purpose: Resolve an agent by model id, approach it, and send a dialog id after interaction.
          UserDescription: Use this when a known model id requires a move, interaction, and a dialog response.
          Notes: Sends the manual dialog id after the interaction succeeds.
        """
        from .agents import BTAgents

        return BTCompositeHelpers.move_target_interact_and_dialog(
            move_tree=BTMovement._move_to_model_id(
                modelID_or_encStr=modelID_or_encStr,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            dialog_id=dialog_id,
            log=log,
        )

    @staticmethod
    def MoveTargetInteractAndAutomaticDialogByModelID(
        modelID_or_encStr: int | str,
        button_number: int = 0,
        pause_on_combat: bool = True,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a tree that resolves an agent by model id, moves to it, interacts, and presses an automatic dialog button.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Move Target Interact And Automatic Dialog By Model ID
          Purpose: Resolve an agent by model id, approach it, and send an automatic dialog choice.
          UserDescription: Use this when a known model id requires a move, interaction, and a visible dialog button selection.
          Notes: Uses the automatic dialog routine after the interaction succeeds.
        """
        from .agents import BTAgents

        return BTCompositeHelpers._interact_and_automatic_dialog(
            move_tree=BTMovement._move_to_model_id(
                modelID_or_encStr=modelID_or_encStr,
                pause_on_combat=pause_on_combat,
                log=log,
            ),
            target_tree=BTAgents.TargetAgentByModelID(modelID_or_encStr=modelID_or_encStr, log=log),
            button_number=button_number,
            log=log,
        )
