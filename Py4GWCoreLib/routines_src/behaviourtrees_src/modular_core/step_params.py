"""
step_params module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Any

from Py4GWCoreLib import Console, ConsoleLog

from .contracts import StepNodeRequest

COMMON_STEP_KEYS: frozenset[str] = frozenset(
    {
        "type",
        "name",
        "repeat",
        "ms",
        "anchor",
        "debug",
        "debug_log",
        "debug_logging",
    }
)

SELECTOR_STEP_KEYS: frozenset[str] = frozenset(
    {
        "point",
        "x",
        "y",
        "npc",
        "enemy",
        "gadget",
        "target",
        "name_contains",
        "enemy_name",
        "agent_name",
        "model_id",
        "nearest",
        "max_dist",
        "exact_name",
        "agent_id",
        "id",
        "item",
    }
)


def _warn_unsupported_param(request: StepNodeRequest, key: str) -> None:
    message = (
        f"Ignored unsupported param {key!r} for step type {request.step_type!r} "
        f"at index {request.step_idx + 1}."
    )
    ConsoleLog("ModularBot", message, Console.MessageType.Warning)
    request.owner.record_diagnostics_event(
        "step_param_ignored",
        phase=request.phase_name,
        step_index=int(request.step_idx + 1),
        step_type=request.step_type,
        message=message,
    )


def _warn_coerce(request: StepNodeRequest, key: str, detail: str) -> None:
    message = (
        f"Param {key!r} for step type {request.step_type!r} at index {request.step_idx + 1} "
        f"used fallback: {detail}"
    )
    ConsoleLog("ModularBot", message, Console.MessageType.Warning)
    request.owner.record_diagnostics_event(
        "step_param_coerced",
        phase=request.phase_name,
        step_index=int(request.step_idx + 1),
        step_type=request.step_type,
        message=message,
    )


def _coerce_common_param(request: StepNodeRequest, key: str, value: Any) -> tuple[bool, Any]:
    if key in ("ms", "repeat"):
        try:
            return True, int(value)
        except Exception:
            _warn_coerce(request, key, "invalid integer, dropping to default")
            return False, None

    if key in ("anchor", "debug", "debug_log", "debug_logging"):
        if isinstance(value, str):
            return True, value.strip().lower() in ("1", "true", "yes", "on")
        if value is None:
            return True, False
        return True, bool(value)

    return True, value


def sanitize_step_params(request: StepNodeRequest, *, allowed_params: tuple[str, ...]) -> dict[str, Any]:
    step = dict(request.step or {})
    allowed = set(COMMON_STEP_KEYS) | set(SELECTOR_STEP_KEYS) | set(allowed_params or ())
    sanitized: dict[str, Any] = {}
    for raw_key, value in step.items():
        key = str(raw_key)
        if key.startswith("_"):
            sanitized[key] = value
            continue
        if key in allowed:
            keep, coerced = _coerce_common_param(request, key, value)
            if keep:
                sanitized[key] = coerced
            continue
        _warn_unsupported_param(request, key)
    return sanitized
