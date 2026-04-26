"""
compose module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from Py4GWCoreLib import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.inventory_recipe import build_auto_inventory_guard_step

from .contracts import StepNodeRequest
from .decorators import with_anchor, with_auto_state_guard, with_post_delay, with_recovery_gate
from .node_registry import get_action_node_builder, get_action_node_spec
from .step_params import sanitize_step_params


def expand_steps(
    *,
    steps: list[dict[str, Any]],
    inventory_guard_source: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    inventory_guard_step = (
        build_auto_inventory_guard_step("modular_block", inventory_guard_source or {})
        if inventory_guard_source is not None
        else None
    )
    if inventory_guard_step and inventory_guard_step.get("check_on_start", True):
        expanded.append(dict(inventory_guard_step))

    for source_idx, source_step in enumerate(steps):
        if not isinstance(source_step, dict):
            continue
        repeat_raw = source_step.get("repeat", 1)
        try:
            repeat = int(repeat_raw)
        except (TypeError, ValueError):
            repeat = 1
        if repeat <= 0:
            continue

        for rep_idx in range(repeat):
            step_to_register = dict(source_step)
            if repeat > 1 and "name" in source_step:
                step_to_register["name"] = f"{source_step['name']} [{rep_idx + 1}/{repeat}]"
            if "_source_index" not in step_to_register:
                step_to_register["_source_index"] = int(source_idx)
            expanded.append(step_to_register)

    return expanded


def _unknown_step_tree(request: StepNodeRequest) -> BehaviorTree:
    def _fail_unknown() -> BehaviorTree.NodeState:
        message = (
            f"Unknown step type {request.step_type!r} at index {request.step_idx} "
            f"for phase={request.phase_name!r}."
        )
        ConsoleLog("ModularBot", message, Console.MessageType.Error)
        request.owner.record_diagnostics_event(
            "step_registration_failed",
            phase=request.phase_name,
            step_index=int(request.step_idx + 1),
            step_type=request.step_type,
            message=message,
        )
        return BehaviorTree.NodeState.FAILURE

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"UnknownStep::{request.step_type}",
            action_fn=_fail_unknown,
            aftercast_ms=0,
        )
    )


def build_action_step_tree(request: StepNodeRequest) -> BehaviorTree:
    from .bootstrap import ensure_action_nodes_bootstrapped

    ensure_action_nodes_bootstrapped()
    builder = get_action_node_builder(request.step_type)
    spec = get_action_node_spec(request.step_type)
    runtime_request = request
    if spec is not None:
        runtime_request = replace(
            request,
            step=sanitize_step_params(request, allowed_params=spec.allowed_params),
        )
    if builder is None:
        core_tree = _unknown_step_tree(request)
    else:
        core_tree = builder(runtime_request)

    # Decorator order: progress -> diagnostics(start) -> guards -> core -> anchor -> delay -> diagnostics(end)
    guarded = with_recovery_gate(core_tree, request)
    guarded = with_auto_state_guard(guarded, request)
    guarded = with_anchor(guarded, request)
    guarded = with_post_delay(guarded, request)

    def _set_progress() -> BehaviorTree.NodeState:
        setattr(request.bot.config, "modular_step_title", request.step_display)
        setattr(request.bot.config, "modular_step_index", max(0, int(request.step_idx + 1)))
        return BehaviorTree.NodeState.SUCCESS

    def _diag_start() -> BehaviorTree.NodeState:
        request.owner.record_diagnostics_event(
            "step_started",
            phase=request.phase_name,
            step_index=int(request.step_idx + 1),
            step_type=request.step_type,
            message=f"Started step type={request.step_type!r} for phase={request.phase_name!r}.",
        )
        return BehaviorTree.NodeState.SUCCESS

    def _diag_end() -> BehaviorTree.NodeState:
        request.owner.record_diagnostics_event(
            "step_finished",
            phase=request.phase_name,
            step_index=int(request.step_idx + 1),
            step_type=request.step_type,
            message=f"Finished step type={request.step_type!r} for phase={request.phase_name!r}.",
        )
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=f"StepSequence::{request.step_type}",
            children=[
                BehaviorTree.ActionNode(
                    name=f"StepProgress::{request.step_type}",
                    action_fn=_set_progress,
                    aftercast_ms=0,
                ),
                BehaviorTree.ActionNode(
                    name=f"StepDiagStart::{request.step_type}",
                    action_fn=_diag_start,
                    aftercast_ms=0,
                ),
                BehaviorTree.SubtreeNode(
                    name=f"StepCore::{request.step_type}",
                    subtree_fn=lambda _node, _tree=guarded: _tree,
                ),
                BehaviorTree.ActionNode(
                    name=f"StepDiagEnd::{request.step_type}",
                    action_fn=_diag_end,
                    aftercast_ms=0,
                ),
            ],
        )
    )
