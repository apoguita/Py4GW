"""
execution_plan module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .source_loader import BlockSourceLoader
from .step_models import parse_step_specs


@dataclass(frozen=True)
class CompiledExecutionPlan:
    """
    C om pi le dE xe cu ti on Pl an class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Compiled Execution Plan
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    block_name: str
    kind: str
    recipe_name: str
    display_name: str
    steps: list[dict[str, Any]]
    source_data: dict[str, Any]


def _coerce_required_hero_names(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        value = raw.strip()
        return [value] if value else []
    if isinstance(raw, list):
        result: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            value = item.strip()
            if value and value not in result:
                result.append(value)
        return result
    return []


def _inject_required_hero_names(steps: list[dict[str, Any]], required_hero_names: list[str]) -> list[dict[str, Any]]:
    if not required_hero_names:
        return steps
    output: list[dict[str, Any]] = []
    for step in steps:
        if str(step.get("type", "")).strip().lower() != "load_party":
            output.append(step)
            continue
        updated = dict(step)
        existing = _coerce_required_hero_names(updated.get("required_hero"))
        merged: list[str] = []
        for name in required_hero_names + existing:
            if name not in merged:
                merged.append(name)
        updated["required_hero"] = merged
        output.append(updated)
    return output


def _inject_load_party_overrides(steps: list[dict[str, Any]], overrides: dict[str, Any]) -> list[dict[str, Any]]:
    if not overrides:
        return steps
    output: list[dict[str, Any]] = []
    for step in steps:
        if str(step.get("type", "")).strip().lower() != "load_party":
            output.append(step)
            continue
        updated = dict(step)
        for key, value in overrides.items():
            updated[str(key)] = value
        output.append(updated)
    return output


def build_execution_plan(
    block_name: str,
    *,
    kind: Optional[str] = None,
    recipe_name: str = "ModularBlock",
    load_party_overrides: Optional[dict[str, Any]] = None,
) -> CompiledExecutionPlan:
    loaded = BlockSourceLoader.load(block_name, kind=kind)
    data = loaded.data
    display_name = str(data.get("name", block_name) or block_name)
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list):
        raw_steps = []

    step_specs = parse_step_specs(raw_steps, source_name=f"{loaded.kind or 'block'}/{loaded.key or block_name}")
    steps = [step.to_runtime_dict() for step in step_specs]

    required_hero_names = _coerce_required_hero_names(data.get("required_hero"))
    steps = _inject_required_hero_names(steps, required_hero_names)
    if load_party_overrides:
        steps = _inject_load_party_overrides(steps, dict(load_party_overrides))

    return CompiledExecutionPlan(
        block_name=str(block_name),
        kind=str(kind or loaded.kind or ""),
        recipe_name=str(recipe_name),
        display_name=display_name,
        steps=[dict(step) for step in steps if isinstance(step, dict)],
        source_data=dict(data) if isinstance(data, dict) else {},
    )
