"""
step_models module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..domain.contracts import SelectorSpec, StepSpec


@dataclass(frozen=True)
class StepParseError:
    """
    S te pP ar se Er ro r class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Step Parse Error
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    index: int
    message: str


def _parse_selector(step: dict[str, Any]) -> SelectorSpec:
    selector_kind = ""
    selector_key = ""
    for kind in ("npc", "enemy", "gadget"):
        value = str(step.get(kind, "") or "").strip()
        if value:
            selector_kind = kind
            selector_key = value
            break
    model_raw = step.get("model_id", None)
    model_id = None
    if model_raw is not None:
        try:
            model_id = int(str(model_raw), 0)
        except Exception:
            model_id = None

    max_dist = None
    if "max_dist" in step:
        try:
            max_dist = float(step.get("max_dist"))
        except Exception:
            max_dist = None

    return SelectorSpec(
        kind=selector_kind,
        key=selector_key,
        target_name=str(step.get("target", step.get("name_contains", "")) or "").strip(),
        model_id=model_id,
        nearest=bool(step.get("nearest", False)),
        exact_name=bool(step.get("exact_name", False)),
        max_dist=max_dist,
    )


def parse_step_specs(raw_steps: list[Any], *, source_name: str) -> list[StepSpec]:
    parsed: list[StepSpec] = []
    errors: list[StepParseError] = []

    for idx, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            errors.append(StepParseError(index=idx, message=f"{source_name} step#{idx} must be an object"))
            continue

        step_type = str(raw_step.get("type", "") or "").strip()
        if not step_type:
            errors.append(StepParseError(index=idx, message=f"{source_name} step#{idx} missing non-empty 'type'"))
            continue

        step = dict(raw_step)
        parsed.append(
            StepSpec(
                step_type=step_type,
                name=str(step.get("name", "") or "").strip(),
                raw=step,
                selector=_parse_selector(step),
            )
        )

    if errors:
        message = "\n".join(error.message for error in errors[:20])
        if len(errors) > 20:
            message += f"\n... {len(errors) - 20} more"
        raise ValueError(message)

    return parsed
