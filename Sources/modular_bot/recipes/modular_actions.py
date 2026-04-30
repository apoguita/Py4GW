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
from .step_utils import log_recipe, parse_step_bool, register_step_title, step_display_name


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
    anchor_after_step = parse_step_bool(step.get("anchor", False), False)

    handler = STEP_HANDLERS.get(step_type)
    if handler is None:
        log_recipe(ctx, f"Unknown step type: {step_type!r} at index {step_idx}")
        return

    fsm = bot.config.FSM
    pre_handler_state_count = len(getattr(fsm, "states", []))
    handler(ctx)

    if anchor_after_step:
        states = list(getattr(fsm, "states", []))
        target_state_name = ""
        if len(states) > pre_handler_state_count:
            # Anchor to the final state emitted by this step handler.
            target_state_name = str(getattr(states[-1], "name", "") or "").strip()
        elif states:
            # Fallback: at least keep recovery close to current registration point.
            target_state_name = str(getattr(states[-1], "name", "") or "").strip()

        def _set_step_anchor(_target: str = target_state_name, _display: str = ctx.step_display) -> None:
            owner = getattr(bot, "_modular_owner", None)
            if owner is None or not hasattr(owner, "set_anchor"):
                return
            if _target:
                owner.set_anchor(_target)
                return
            # Last-resort fallback when no concrete state target is available.
            owner.set_anchor(_display)

        bot.States.AddCustomState(_set_step_anchor, f"Set Anchor (Step): {ctx.step_display}")
