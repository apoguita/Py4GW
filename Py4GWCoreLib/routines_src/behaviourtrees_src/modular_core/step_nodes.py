"""
step_nodes module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from collections.abc import Callable
import traceback
from dataclasses import dataclass

from Py4GWCoreLib import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from .contracts import StepNodeRequest
from .step_actions import StepActionHandler
from .step_context import StepContext


def _fail_log(message: str, *, message_type=Console.MessageType.Error) -> None:
    ConsoleLog("ModularBot", message, message_type)


def _build_step_context(request: StepNodeRequest) -> StepContext:
    runtime_step = dict(request.step)
    # Step delay is handled by the BT post-delay decorator.
    runtime_step["ms"] = 0
    return StepContext(
        bot=request.bot,
        step=runtime_step,
        step_idx=int(request.step_idx),
        recipe_name=request.recipe_name,
        step_type=request.step_type,
        step_display=request.step_display,
    )


@dataclass
class _StepNodeRuntimeAction:
    """
    Runtime action wrapper that executes one step handler through the FSM.

    Meta:
      Expose: true
      Audience: advanced
      Display: Step Node Runtime Action
      Purpose: Execute one modular step handler and drive its registered FSM states.
      UserDescription: Internal callable used by action tree builders to run modular step handlers.
      Notes: Handles start/tick lifecycle, recovery pauses, and diagnostics on failure.
    """

    request: StepNodeRequest
    handler: StepActionHandler
    started: bool = False
    done: bool = False
    _death_pause_logged: bool = False

    def _fail(self, message: str, *, traceback_text: str = "") -> BehaviorTree.NodeState:
        owner = self.request.owner
        _fail_log(message, message_type=Console.MessageType.Error)
        owner.record_diagnostics_event(
            "exception",
            phase=self.request.phase_name,
            step_index=int(self.request.step_idx + 1),
            step_type=self.request.step_type,
            message=message,
            traceback_text=traceback_text,
        )
        self.done = True
        return BehaviorTree.NodeState.FAILURE

    def _start_runtime(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        owner = self.request.owner
        owner._reset_step_fsm()
        try:
            self.handler(_build_step_context(self.request))
        except Exception as exc:
            return self._fail(
                (
                    f"Step registration failed for phase={self.request.phase_name!r}, "
                    f"idx={self.request.step_idx + 1}, type={self.request.step_type!r}: {exc}"
                ),
                traceback_text=traceback.format_exc(),
            )

        fsm = self.request.bot.config.FSM
        try:
            state_names = list(getattr(fsm, "get_state_names", lambda: [])() or [])
        except Exception:
            state_names = []
        if state_names:
            node.blackboard["modular_last_registered_state_name"] = str(state_names[-1] or "")

        state_count = int(getattr(fsm, "get_state_count", lambda: 0)() or 0)
        if state_count <= 0:
            self.done = True
            return BehaviorTree.NodeState.SUCCESS

        try:
            fsm.start()
        except Exception as exc:
            return self._fail(
                (
                    f"Step start failed for phase={self.request.phase_name!r}, "
                    f"idx={self.request.step_idx + 1}, type={self.request.step_type!r}: {exc}"
                ),
                traceback_text=traceback.format_exc(),
            )

        self.started = True
        restart_state = str(self.request.restart_state or "").strip()
        if restart_state:
            try:
                if fsm.has_state(restart_state):
                    fsm.jump_to_state_by_name(restart_state)
                    owner._debug_log(
                        (
                            f"Resumed phase={self.request.phase_name!r} step idx={self.request.step_idx + 1} "
                            f"from state {restart_state!r}."
                        ),
                    )
            except Exception:
                pass
        return BehaviorTree.NodeState.RUNNING

    def __call__(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        owner = self.request.owner
        if self.done:
            return BehaviorTree.NodeState.SUCCESS

        if owner._pending_recovery is not None:
            return BehaviorTree.NodeState.RUNNING
        if owner._on_death is None and owner._is_player_dead():
            if not self._death_pause_logged:
                owner._debug_log("[Player death] Pausing step execution until revive.")
                self._death_pause_logged = True
            return BehaviorTree.NodeState.RUNNING
        self._death_pause_logged = False

        if not self.started:
            start_state = self._start_runtime(node)
            if start_state != BehaviorTree.NodeState.RUNNING:
                return start_state

        fsm = self.request.bot.config.FSM
        owner._tick_bot_coroutines()
        try:
            fsm.update()
        except Exception as exc:
            return self._fail(
                (
                    f"Step runtime tick failed for phase={self.request.phase_name!r}, "
                    f"idx={self.request.step_idx + 1}, type={self.request.step_type!r}: {exc}"
                ),
                traceback_text=traceback.format_exc(),
            )

        if bool(getattr(fsm, "is_finished", lambda: False)()):
            self.done = True
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING


def build_function_step_tree(request: StepNodeRequest, handler: StepActionHandler) -> BehaviorTree:
    """Build a behavior tree action node for one function-based step handler."""
    if not callable(handler):
        raise TypeError("handler must be callable")
    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"Action::{request.step_type}",
            action_fn=_StepNodeRuntimeAction(request=request, handler=handler),
            aftercast_ms=0,
        )
    )


def probe_state_names_for_handler(request: StepNodeRequest, handler: StepActionHandler) -> list[str]:
    """Probe FSM state names by executing a step handler against a reset FSM."""
    owner = request.owner
    owner._reset_step_fsm()
    try:
        handler(_build_step_context(request))
    except Exception:
        owner._reset_step_fsm()
        return []

    fsm = request.bot.config.FSM
    try:
        names = list(getattr(fsm, "get_state_names", lambda: [])() or [])
    except Exception:
        names = []
    owner._reset_step_fsm()
    return [str(name) for name in names if str(name or "").strip()]


def make_step_node_builder(handler: StepActionHandler) -> Callable[[StepNodeRequest], BehaviorTree]:
    """Create a reusable step node builder for a step handler."""
    if not callable(handler):
        raise TypeError("handler must be callable")

    def _builder(request: StepNodeRequest) -> BehaviorTree:
        return build_function_step_tree(request, handler)

    return _builder


def make_state_name_probe(handler: StepActionHandler) -> Callable[[StepNodeRequest], list[str]]:
    """Create a reusable state-name probe for a step handler."""
    if not callable(handler):
        raise TypeError("handler must be callable")

    def _probe(request: StepNodeRequest) -> list[str]:
        return probe_state_names_for_handler(request, handler)

    return _probe
