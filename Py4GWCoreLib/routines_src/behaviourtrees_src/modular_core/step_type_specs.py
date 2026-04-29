"""
Declarative step type specification model for modular core action registration.

This module defines the canonical step registration contract used by modular
core subsystems.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .node_registry import StateNameProbe, StepNodeBuilder
from .step_actions import StepActionHandler


def normalize_allowed_params(allowed_params: Iterable[str] | None) -> tuple[str, ...]:
    """Normalize and sort allowed parameter names."""
    if allowed_params is None:
        return ()
    return tuple(sorted(str(name) for name in allowed_params if str(name).strip()))


@dataclass(frozen=True)
class StepTypeSpec:
    """
    Declarative specification for one modular step type.

    Meta:
      Expose: true
      Audience: advanced
      Display: Step Type Spec
      Purpose: Define one step type runtime contract for registry/bootstrap wiring.
      UserDescription: Internal model used to register modular action step types without boilerplate node classes.
      Notes: Holds canonical step metadata including handler and allowed params.
    """

    step_type: str
    handler: StepActionHandler
    allowed_params: tuple[str, ...]
    node_class_name: str
    explicit_builder: bool = True
    builder: StepNodeBuilder | None = None
    state_name_probe: StateNameProbe | None = None
    metadata: dict[str, Any] | None = None


def build_step_type_spec(
    step_type: str,
    handler: StepActionHandler,
    *,
    allowed_params: Iterable[str] | None = None,
    node_class_name: str = "",
    explicit_builder: bool = True,
    builder: StepNodeBuilder | None = None,
    state_name_probe: StateNameProbe | None = None,
    metadata: dict[str, Any] | None = None,
) -> StepTypeSpec:
    """Create a normalized ``StepTypeSpec`` instance."""
    key = str(step_type or "").strip()
    if not key:
        raise ValueError("step_type cannot be empty")
    if not callable(handler):
        raise TypeError("handler must be callable")
    return StepTypeSpec(
        step_type=key,
        handler=handler,
        allowed_params=normalize_allowed_params(allowed_params),
        node_class_name=str(node_class_name or ""),
        explicit_builder=bool(explicit_builder),
        builder=builder if callable(builder) else None,
        state_name_probe=state_name_probe if callable(state_name_probe) else None,
        metadata=dict(metadata or {}) if metadata else None,
    )


def register_step_type_specs(
    step_specs: Iterable[StepTypeSpec],
    *,
    overwrite: bool = False,
) -> None:
    """
    Register a collection of declarative step type specifications.
    """
    from .node_registry import register_action_node
    from .step_nodes import make_state_name_probe, make_step_node_builder

    for spec in step_specs:
        if not isinstance(spec, StepTypeSpec):
            raise TypeError("step_specs must contain StepTypeSpec entries")
        builder = spec.builder if callable(spec.builder) else make_step_node_builder(spec.handler)
        state_name_probe = (
            spec.state_name_probe
            if callable(spec.state_name_probe)
            else make_state_name_probe(spec.handler)
        )
        register_action_node(
            spec.step_type,
            builder,
            overwrite=overwrite,
            node_class_name=spec.node_class_name,
            allowed_params=spec.allowed_params,
            explicit_builder=bool(spec.explicit_builder),
            state_name_probe=state_name_probe,
            runtime_handler=spec.handler,
            metadata=spec.metadata,
        )
