"""
contracts module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class SelectorSpec:
    """
    S el ec to rS pe c class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Selector Spec
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    kind: str = ""
    key: str = ""
    target_name: str = ""
    model_id: Optional[int] = None
    nearest: bool = False
    exact_name: bool = False
    max_dist: Optional[float] = None


@dataclass(frozen=True)
class StepSpec:
    """
    S te pS pe c class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Step Spec
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    step_type: str
    name: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    selector: SelectorSpec = field(default_factory=SelectorSpec)

    def to_runtime_dict(self) -> dict[str, Any]:
        return dict(self.raw)


@dataclass(frozen=True)
class ModularPhaseRuntimeSpec:
    """
    M od ul ar Ph as eR un ti me Sp ec class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Modular Phase Runtime Spec
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    block_name: str = ""
    kind: str = ""
    recipe_name: str = "ModularBlock"
    load_party_overrides: dict[str, Any] = field(default_factory=dict)
    inline_plan: Optional[dict[str, Any]] = None
    pre_run_hook: Optional[Callable[[Any], None]] = None
    pre_run_name: str = ""
    post_run_hook: Optional[Callable[[Any], None]] = None
    post_run_name: str = ""
