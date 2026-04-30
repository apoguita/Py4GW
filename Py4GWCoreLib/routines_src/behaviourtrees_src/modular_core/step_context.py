"""
step_context module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


@dataclass(frozen=True)
class StepContext:
    """
    S te pC on te xt class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Step Context
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    bot: "Botting"
    step: Dict[str, Any]
    step_idx: int
    recipe_name: str
    step_type: str
    step_display: str
