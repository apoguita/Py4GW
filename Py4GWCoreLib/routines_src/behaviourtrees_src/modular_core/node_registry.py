"""
node_registry module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from .contracts import StepNodeRequest
from .step_actions import StepActionHandler


StepNodeBuilder = Callable[[StepNodeRequest], BehaviorTree]
StateNameProbe = Callable[[StepNodeRequest], list[str]]


@dataclass(frozen=True)
class ActionNodeSpec:
    """
    Runtime metadata for one registered modular step type.

    Meta:
      Expose: true
      Audience: advanced
      Display: Action Node Spec
      Purpose: Describe a registered step type and its runtime contract metadata.
      UserDescription: Internal metadata used by modular orchestration and direct step execution helpers.
      Notes: Includes optional runtime handler and metadata used by runtime APIs.
    """

    step_type: str
    builder_name: str
    builder_module: str
    node_class_name: str
    allowed_params: tuple[str, ...]
    explicit_builder: bool
    state_name_probe: StateNameProbe | None = None
    runtime_handler: StepActionHandler | None = None
    metadata: dict[str, Any] | None = None

_ACTION_NODE_BUILDERS: dict[str, StepNodeBuilder] = {}
_ACTION_NODE_SPECS: dict[str, ActionNodeSpec] = {}


def register_action_node(
    step_type: str,
    builder: StepNodeBuilder,
    *,
    overwrite: bool = False,
    node_class_name: str | None = None,
    allowed_params: set[str] | tuple[str, ...] | list[str] | None = None,
    explicit_builder: bool = False,
    state_name_probe: StateNameProbe | None = None,
    runtime_handler: StepActionHandler | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Register one ``step_type -> builder`` mapping and runtime metadata."""
    key = str(step_type or "").strip()
    if not key:
        raise ValueError("step_type cannot be empty")
    if not callable(builder):
        raise TypeError("builder must be callable")
    if (not overwrite) and key in _ACTION_NODE_BUILDERS:
        raise ValueError(f"Action node already registered for step type: {key!r}")

    allowed = tuple(sorted(str(name) for name in (allowed_params or ()) if str(name).strip()))
    spec = ActionNodeSpec(
        step_type=key,
        builder_name=str(getattr(builder, "__name__", "")),
        builder_module=str(getattr(builder, "__module__", "")),
        node_class_name=str(node_class_name or ""),
        allowed_params=allowed,
        explicit_builder=bool(explicit_builder),
        state_name_probe=state_name_probe if callable(state_name_probe) else None,
        runtime_handler=runtime_handler if callable(runtime_handler) else None,
        metadata=dict(metadata or {}) if metadata else None,
    )
    _ACTION_NODE_BUILDERS[key] = builder
    _ACTION_NODE_SPECS[key] = spec


def get_action_node_builder(step_type: str) -> StepNodeBuilder | None:
    return _ACTION_NODE_BUILDERS.get(str(step_type or "").strip())


def get_action_node_builders() -> dict[str, StepNodeBuilder]:
    return dict(_ACTION_NODE_BUILDERS)


def get_action_node_spec(step_type: str) -> ActionNodeSpec | None:
    return _ACTION_NODE_SPECS.get(str(step_type or "").strip())


def get_action_node_specs() -> dict[str, ActionNodeSpec]:
    return dict(_ACTION_NODE_SPECS)


def get_registered_step_types() -> tuple[str, ...]:
    return tuple(sorted(_ACTION_NODE_BUILDERS.keys()))


def clear_action_node_builders() -> None:
    _ACTION_NODE_BUILDERS.clear()
    _ACTION_NODE_SPECS.clear()
