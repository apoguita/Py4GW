"""
registry module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core import (
    ensure_action_nodes_bootstrapped,
    get_action_node_builder,
    get_action_node_builders,
    get_action_node_spec,
    get_action_node_specs as _get_action_node_specs,
    get_registered_step_types as _get_registered_step_types,
    register_action_node as _register_action_node,
)


def _ensure_registry() -> None:
    ensure_action_nodes_bootstrapped()


def get_registered_step_types() -> tuple[str, ...]:
    _ensure_registry()
    return _get_registered_step_types()


def get_action_node(step_type: str):
    _ensure_registry()
    return get_action_node_builder(step_type)


def get_action_nodes():
    _ensure_registry()
    return get_action_node_builders()


def get_action_node_metadata(step_type: str):
    _ensure_registry()
    return get_action_node_spec(step_type)


def get_action_node_specs():
    _ensure_registry()
    return _get_action_node_specs()


def register_action_node(step_type: str, builder, *, overwrite: bool = False, **kwargs) -> None:
    """
    Register a modular step builder and optional direct runtime contract.

    Meta:
      Expose: true
      Audience: advanced
      Display: Register Action Node
      Purpose: Register a step-type builder for behavior-tree execution.
      UserDescription: Use this to add or override step types in the modular action registry.
      Notes: Optional runtime_handler/runtime_allowed_params enable direct run_step support for custom step types.
    """
    runtime_handler = kwargs.pop("runtime_handler", None)
    runtime_allowed_params = kwargs.pop("runtime_allowed_params", None)
    if runtime_allowed_params is not None and "allowed_params" not in kwargs:
        # Keep planner-path sanitization aligned with direct runtime execution.
        kwargs["allowed_params"] = runtime_allowed_params
    _ensure_registry()
    _register_action_node(
        step_type,
        builder,
        overwrite=overwrite,
        runtime_handler=runtime_handler,
        **kwargs,
    )
