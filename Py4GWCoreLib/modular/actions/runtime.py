"""
Modular action runtime helpers
==============================

This module provides direct step execution helpers for modular actions without
building a full planner tree. It keeps the same step sanitization contract used
by modular-core runtime execution and supports explicit runtime extension
registration for custom action types.

Authoring conventions
---------------------
- Keep public APIs stable: `register_runtime_action`, `run_step`, `run_steps`.
- Keep extension behavior explicit through a runtime handler contract.
- Keep internal shims and caches private with a leading underscore.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from Py4GWCoreLib.routines_src.behaviourtrees_src import modular_core
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.contracts import StepNodeRequest
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_nodes import make_step_node_builder
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_context import StepContext
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_params import sanitize_step_params


StepHandler = Callable[[StepContext], None]


class _StandaloneOwner:
    """
    Minimal owner shim used by `run_step` when a ModularBot owner is not present.
    """

    def record_diagnostics_event(self, *_args, **_kwargs) -> None:
        return None

    def set_anchor(self, _target: str) -> bool:
        return False


def _normalize_allowed_params(allowed_params: Iterable[str] | None) -> tuple[str, ...]:
    if allowed_params is None:
        return ()
    return tuple(sorted(str(name) for name in allowed_params if str(name).strip()))


def register_runtime_action(
    step_type: str,
    handler: StepHandler,
    *,
    allowed_params: Iterable[str] | None = None,
    overwrite: bool = False,
) -> None:
    """
    Register a direct runtime handler for `run_step`/`run_steps`.

    Meta:
      Expose: true
      Audience: advanced
      Display: Register Runtime Action
      Purpose: Attach a direct handler contract to a modular step type.
      UserDescription: Use this when a step type should be executable via run_step without a full planner tree.
      Notes: Supports overwrite semantics and explicit allowed_params used by sanitize_step_params.
    """
    key = str(step_type or "").strip()
    if not key:
        raise ValueError("step_type cannot be empty")
    if not callable(handler):
        raise TypeError("runtime handler must be callable")

    modular_core.ensure_action_nodes_bootstrapped()
    existing = modular_core.get_action_node_spec(key)
    if (not overwrite) and existing is not None:
        raise ValueError(f"Runtime action already registered for step type: {key!r}")

    allowed = _normalize_allowed_params(allowed_params)
    modular_core.register_action_node(
        key,
        make_step_node_builder(handler),
        overwrite=overwrite,
        allowed_params=allowed,
        runtime_handler=handler,
    )


def _resolve_runtime_definition(step: dict[str, Any]) -> tuple[str, StepHandler, tuple[str, ...]]:
    step_type = str(step.get("type", "") or "").strip()
    if not step_type:
        raise ValueError("step must include non-empty 'type'")

    modular_core.ensure_action_nodes_bootstrapped()
    spec = modular_core.get_action_node_spec(step_type)
    if spec is not None:
        runtime_handler = getattr(spec, "runtime_handler", None)
        if callable(runtime_handler):
            allowed_params = tuple(sorted(str(name) for name in (spec.allowed_params or ()) if str(name)))
            return step_type, runtime_handler, allowed_params
        raise ValueError(
            "Step type is registered for behavior-tree execution but has no direct runtime handler: "
            f"{step_type!r}. Register it via "
            "register_action_node(..., runtime_handler=..., runtime_allowed_params=...)."
        )
    raise ValueError(f"Unknown modular step type: {step_type!r}")


def _build_step_context(
    bot: Any,
    step: dict[str, Any],
    *,
    step_type: str,
    allowed_params: tuple[str, ...],
    recipe_name: str,
    step_idx: int,
    step_total: int | None,
    phase_name: str,
) -> StepContext:
    owner = getattr(bot, "_modular_owner", None)
    if owner is None:
        owner = _StandaloneOwner()

    total = int(step_total) if step_total is not None else 1
    total = max(1, total)
    idx = max(0, int(step_idx))
    recipe = str(recipe_name or "ModularStep")
    display = str(step.get("name", step_type))

    request = StepNodeRequest(
        owner=owner,
        bot=bot,
        phase_name=str(phase_name or ""),
        recipe_name=recipe,
        step=dict(step),
        step_idx=idx,
        step_total=total,
        step_type=step_type,
        step_display=display,
        restart_state="",
    )
    sanitized_step = sanitize_step_params(request, allowed_params=allowed_params)
    return StepContext(
        bot=bot,
        step=sanitized_step,
        step_idx=idx,
        recipe_name=recipe,
        step_type=step_type,
        step_display=display,
    )


def run_step(
    bot: Any,
    step: dict[str, Any],
    *,
    recipe_name: str,
    step_idx: int = 0,
    step_total: int | None = None,
    phase_name: str = "",
) -> None:
    """
    Execute one modular action step directly.

    Meta:
      Expose: true
      Audience: intermediate
      Display: Run Step
      Purpose: Execute a single modular action step with parameter sanitization.
      UserDescription: Use this to run one modular step dict directly from widgets or scripts.
      Notes: Raises if step type is unknown or lacks a runtime handler contract.
    """
    if not isinstance(step, dict):
        raise TypeError("step must be a dict")

    step_type, handler, allowed_params = _resolve_runtime_definition(step)
    ctx = _build_step_context(
        bot,
        step,
        step_type=step_type,
        allowed_params=allowed_params,
        recipe_name=recipe_name,
        step_idx=step_idx,
        step_total=step_total,
        phase_name=phase_name,
    )
    handler(ctx)


def run_steps(
    bot: Any,
    steps: list[dict[str, Any]],
    *,
    recipe_name: str,
    phase_name: str = "",
) -> None:
    """
    Execute a list of modular action steps directly.

    Meta:
      Expose: true
      Audience: intermediate
      Display: Run Steps
      Purpose: Execute multiple modular steps in-order with strict input validation.
      UserDescription: Use this to run a sequence of step dicts without building a planner.
      Notes: Fails fast when any step entry is not a dict.
    """
    if not isinstance(steps, list):
        raise TypeError("steps must be a list of step dicts")

    total = int(len(steps))
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            raise TypeError(f"steps[{idx}] must be a dict")
        run_step(
            bot,
            step,
            recipe_name=recipe_name,
            step_idx=idx,
            step_total=total,
            phase_name=phase_name,
        )
