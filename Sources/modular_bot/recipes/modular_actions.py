"""
Shared step-action dispatcher for modular mission/quest recipes.

This file defines the union of actions supported by mission and quest recipes.
Every action supports an optional ``ms`` delay after execution (default: 100ms),
except ``wait`` where ``ms`` is the action itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from .action_registry import STEP_HANDLERS
from .step_context import StepContext
from .step_utils import log_recipe, register_step_title, step_display_name


def register_step(bot: "Botting", step: Dict[str, Any], step_idx: int, recipe_name: str) -> None:
    """Register one JSON step onto the bot FSM."""
    step_type = str(step.get("type", "")).strip()
    if not step_type:
        log_recipe(
            StepContext(
                bot=bot,
                step=step,
                step_idx=step_idx,
                recipe_name=recipe_name,
                step_type="",
                step_display=f"Step {step_idx + 1}",
            ),
            f"Missing step type at index {step_idx}",
        )
        return

    ctx = StepContext(
        bot=bot,
        step=step,
        step_idx=step_idx,
        recipe_name=recipe_name,
        step_type=step_type,
        step_display=step_display_name(step, step_type, step_idx),
    )
    register_step_title(ctx)

    handler = STEP_HANDLERS.get(step_type)
    if handler is None:
        log_recipe(ctx, f"Unknown step type: {step_type!r} at index {step_idx}")
        return

    handler(ctx)
