"""
contracts module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StepNodeRequest:
    """
    S te pN od eR eq ue st class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Step Node Request
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    owner: Any
    bot: Any
    phase_name: str
    recipe_name: str
    step: dict[str, Any]
    step_idx: int
    step_total: int
    step_type: str
    step_display: str
    restart_state: str = ""
