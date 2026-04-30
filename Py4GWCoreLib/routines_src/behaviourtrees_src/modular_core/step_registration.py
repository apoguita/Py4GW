"""
Decorator-driven modular step registration helpers.

This module provides the canonical decorator-first step registration contract
for staged modular core action handlers.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable

from .node_registry import StateNameProbe, StepNodeBuilder
from .step_actions import StepActionHandler
from .step_type_specs import StepTypeSpec, build_step_type_spec, normalize_allowed_params, register_step_type_specs


_STEP_BINDINGS_ATTR = "__modular_step_bindings__"
_DECORATED_ACTION_MODULES: tuple[str, ...] = (
    ".actions_interaction",
    ".actions_inventory_handlers",
    ".actions_inventory_merchanting",
    ".actions_movement",
    ".actions_party",
    ".actions_party_toggles",
    ".actions_targeting",
)


@dataclass(frozen=True)
class ModularStepBinding:
    """Decorator metadata attached to one step action handler."""

    step_type: str
    category: str
    allowed_params: tuple[str, ...]
    node_class_name: str
    explicit_builder: bool = True
    builder: StepNodeBuilder | None = None
    state_name_probe: StateNameProbe | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class _BindingRecord:
    module_name: str
    function_name: str
    function_line: int
    binding_index: int
    handler: StepActionHandler
    binding: ModularStepBinding


def modular_step(
    *,
    step_type: str,
    category: str,
    allowed_params: Iterable[str] | None = None,
    node_class_name: str = "",
    explicit_builder: bool = True,
    builder: StepNodeBuilder | None = None,
    state_name_probe: StateNameProbe | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[StepActionHandler], StepActionHandler]:
    """
    Attach one declarative modular step binding to a handler function.
    """

    normalized_step_type = str(step_type or "").strip()
    if not normalized_step_type:
        raise ValueError("step_type cannot be empty")
    normalized_category = str(category or "").strip().lower()
    if not normalized_category:
        raise ValueError("category cannot be empty")

    binding = ModularStepBinding(
        step_type=normalized_step_type,
        category=normalized_category,
        allowed_params=normalize_allowed_params(allowed_params),
        node_class_name=str(node_class_name or ""),
        explicit_builder=bool(explicit_builder),
        builder=builder if callable(builder) else None,
        state_name_probe=state_name_probe if callable(state_name_probe) else None,
        metadata=dict(metadata or {}) if metadata else None,
    )

    def _decorate(handler: StepActionHandler) -> StepActionHandler:
        if not callable(handler):
            raise TypeError("modular_step target must be callable")
        existing = tuple(getattr(handler, _STEP_BINDINGS_ATTR, ()))
        setattr(handler, _STEP_BINDINGS_ATTR, existing + (binding,))
        return handler

    return _decorate


def get_handler_step_bindings(handler: StepActionHandler) -> tuple[ModularStepBinding, ...]:
    """Return decorator bindings attached to a handler."""
    return tuple(getattr(handler, _STEP_BINDINGS_ATTR, ()))


def _resolve_module_name(module_name: str) -> str:
    name = str(module_name or "").strip()
    if not name:
        raise ValueError("module_name cannot be empty")
    if name.startswith("."):
        return f"{__package__}{name}"
    return name


def _iter_module_binding_records(module: ModuleType) -> list[_BindingRecord]:
    records: list[_BindingRecord] = []
    seen_handler_ids: set[int] = set()
    for symbol in module.__dict__.values():
        if not callable(symbol):
            continue
        handler_id = id(symbol)
        if handler_id in seen_handler_ids:
            continue
        seen_handler_ids.add(handler_id)
        bindings = get_handler_step_bindings(symbol)
        if not bindings:
            continue
        line = int(getattr(getattr(symbol, "__code__", None), "co_firstlineno", 0) or 0)
        fn_name = str(getattr(symbol, "__name__", "<anonymous>"))
        for idx, binding in enumerate(bindings):
            records.append(
                _BindingRecord(
                    module_name=str(module.__name__),
                    function_name=fn_name,
                    function_line=line,
                    binding_index=int(idx),
                    handler=symbol,
                    binding=binding,
                )
            )
    return records


def _collect_binding_records(
    *,
    categories: Iterable[str] | None = None,
    module_names: Iterable[str] | None = None,
) -> list[_BindingRecord]:
    normalized_categories = {
        str(category or "").strip().lower() for category in (categories or ()) if str(category or "").strip()
    }
    selected_module_names = tuple(
        _resolve_module_name(module_name)
        for module_name in (module_names if module_names is not None else _DECORATED_ACTION_MODULES)
    )

    records: list[_BindingRecord] = []
    for module_name in selected_module_names:
        module = import_module(module_name)
        for record in _iter_module_binding_records(module):
            if normalized_categories and record.binding.category not in normalized_categories:
                continue
            records.append(record)

    records.sort(
        key=lambda record: (
            record.module_name,
            record.function_line,
            record.function_name,
            record.binding_index,
            record.binding.step_type,
        )
    )

    seen_step_types: dict[str, _BindingRecord] = {}
    for record in records:
        step_type = record.binding.step_type
        if step_type not in seen_step_types:
            seen_step_types[step_type] = record
            continue
        first = seen_step_types[step_type]
        raise ValueError(
            "Duplicate modular step_type binding "
            f"{step_type!r}: {first.module_name}:{first.function_name} "
            f"and {record.module_name}:{record.function_name}"
        )

    return records


def get_decorated_step_specs(
    *,
    categories: Iterable[str] | None = None,
    module_names: Iterable[str] | None = None,
) -> tuple[StepTypeSpec, ...]:
    """
    Build declarative ``StepTypeSpec`` entries from decorated action handlers.
    """
    specs: list[StepTypeSpec] = []
    for record in _collect_binding_records(categories=categories, module_names=module_names):
        binding = record.binding
        specs.append(
            build_step_type_spec(
                binding.step_type,
                record.handler,
                allowed_params=binding.allowed_params,
                node_class_name=binding.node_class_name,
                explicit_builder=binding.explicit_builder,
                builder=binding.builder,
                state_name_probe=binding.state_name_probe,
                metadata=binding.metadata,
            )
        )
    return tuple(specs)


def register_decorated_step_types(
    *,
    overwrite: bool = False,
    categories: Iterable[str] | None = None,
    module_names: Iterable[str] | None = None,
) -> tuple[StepTypeSpec, ...]:
    """
    Register all decorated step specs for planner/runtime usage.
    """
    specs = get_decorated_step_specs(categories=categories, module_names=module_names)
    register_step_type_specs(specs, overwrite=overwrite)
    return specs


__all__ = [
    "ModularStepBinding",
    "modular_step",
    "get_handler_step_bindings",
    "get_decorated_step_specs",
    "register_decorated_step_types",
]
