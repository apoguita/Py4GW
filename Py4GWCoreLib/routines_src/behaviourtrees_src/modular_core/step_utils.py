"""
step_utils module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .step_context import StepContext

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


DEFAULT_STEP_DELAY_MS = 250


def step_display_name(step: Dict[str, Any], step_type: str, step_idx: int) -> str:
    name = str(step.get("name", "") or "").strip()
    if name:
        return name
    return f"{step_type.replace('_', ' ').title()} {step_idx + 1}"


def parse_step_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return default


def parse_step_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_step_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if value is None:
        return default
    return bool(value)


def parse_step_point(step: Dict[str, Any]) -> tuple[float, float] | None:
    point = step.get("point", None)
    if isinstance(point, (list, tuple)) and len(point) >= 2:
        try:
            return float(point[0]), float(point[1])
        except (TypeError, ValueError):
            return None

    return None


def step_delay_ms(step: Dict[str, Any], default: int = DEFAULT_STEP_DELAY_MS) -> int:
    value = step.get("ms", default)
    try:
        ms = int(value)
    except (TypeError, ValueError):
        ms = default
    return ms if ms > 0 else 0


def wait_after_step(bot: "Botting", step: Dict[str, Any]) -> None:
    ms = step_delay_ms(step)
    if ms > 0:
        bot.Wait.ForTime(ms)


def cutscene_active() -> bool:
    try:
        from Py4GWCoreLib import GLOBAL_CACHE, Map

        return bool(Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.IsInCinematic())
    except Exception:
        return False


def log_recipe(ctx: StepContext, message: str) -> None:
    if not recipe_debug_logging_enabled(ctx):
        return
    from Py4GWCoreLib import ConsoleLog

    ConsoleLog(f"Recipe:{ctx.recipe_name}", message)


def recipe_debug_logging_enabled(ctx: StepContext) -> bool:
    global_enabled = bool(getattr(ctx.bot.config, "modular_debug_logging", False))
    if not global_enabled:
        return False

    step = getattr(ctx, "step", {}) or {}
    if isinstance(step, dict):
        if "debug_logging" in step:
            return parse_step_bool(step.get("debug_logging"), True)
        if "debug_log" in step:
            return parse_step_bool(step.get("debug_log"), True)
        if "debug" in step:
            return parse_step_bool(step.get("debug"), True)

    return True


def debug_log_recipe(ctx: StepContext, message: str) -> None:
    if not recipe_debug_logging_enabled(ctx):
        return
    from Py4GWCoreLib import ConsoleLog

    ConsoleLog(f"Recipe:{ctx.recipe_name}", message)
