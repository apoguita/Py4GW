"""
actions_movement_pathing module

This module provides pathing-oriented modular movement step handlers.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_pathing import (
    add_auto_path_delayed_state,
    add_auto_path_state,
    add_auto_path_till_timeout_state,
    add_patrol_until_enemy_state,
    add_pre_movement_loot_wait_state,
)

from .combat_engine import party_loot_wait_required
from .step_context import StepContext
from .step_selectors import resolve_enemy_agent_id_from_step
from .step_utils import (
    cutscene_active,
    debug_log_recipe,
    log_recipe,
    parse_step_bool,
    parse_step_float,
    parse_step_int,
    wait_after_step,
)


def _add_pre_movement_loot_wait(ctx: StepContext, step_name: str) -> None:
    """
    Pause movement while party loot is pending (for CB/HeroAI runtimes).
    """
    if not parse_step_bool(ctx.step.get("wait_for_loot", True), True):
        return

    wait_timeout_ms = max(0, parse_step_int(ctx.step.get("loot_wait_timeout_ms", 30_000), 30_000))
    poll_ms = max(50, parse_step_int(ctx.step.get("loot_wait_poll_ms", 300), 300))
    loot_range = parse_step_float(ctx.step.get("loot_wait_range", 1_250.0), 1_250.0)

    add_pre_movement_loot_wait_state(
        ctx.bot,
        step_name=str(step_name),
        enabled=True,
        timeout_ms=wait_timeout_ms,
        poll_ms=poll_ms,
        loot_range=loot_range,
        loot_wait_required=party_loot_wait_required,
    )


def _enemy_resolver_for_patrol(ctx: StepContext, max_dist: float, include_dead: bool):
    from Py4GWCoreLib import Agent, AgentArray, Player

    def _resolve_detected_enemy() -> int | None:
        # If step provides a specific selector, reuse shared selector logic.
        has_selector = any(
            key in ctx.step
            for key in ("agent_id", "id", "enemy", "target", "name_contains", "enemy_name", "model_id", "nearest")
        )
        if has_selector:
            return resolve_enemy_agent_id_from_step(
                ctx.step,
                recipe_name=ctx.recipe_name,
                step_idx=ctx.step_idx,
                default_max_dist=max_dist,
            )

        px, py = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, (px, py), max_dist)
        if not include_dead:
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda enemy_id: Agent.IsAlive(enemy_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, (px, py))
        if not enemy_array:
            return None
        return int(enemy_array[0])

    return _resolve_detected_enemy


def handle_auto_path(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"AutoPath {ctx.step_idx + 1}")
    _add_pre_movement_loot_wait(ctx, str(name))
    pause_on_combat_raw = ctx.step.get("pause_on_combat", None)
    if pause_on_combat_raw is None:
        # Default to current pause-on-danger state so movement behavior follows
        # runtime combat mode (combat on => pause movement, combat off => keep moving).
        pause_on_combat = bool(ctx.bot.Properties.IsActive("pause_on_danger"))
    else:
        pause_on_combat = parse_step_bool(pause_on_combat_raw, False)
    pause_on_danger_was_active = bool(ctx.bot.Properties.IsActive("pause_on_danger"))
    default_tolerance = float(ctx.bot.config.config_properties.movement_tolerance.get("value") or 150.0)
    arrival_tolerance = max(25.0, parse_step_float(ctx.step.get("arrival_tolerance", ctx.step.get("tolerance", default_tolerance)), default_tolerance))
    retry_delay_ms = max(50, parse_step_int(ctx.step.get("retry_delay_ms", 350), 350))
    # When False (default), prevent auto_path from silently completing during
    # zone transitions; this avoids advancing to the next waypoint set on the
    # wrong map after failures/reloads.
    allow_map_transition = parse_step_bool(ctx.step.get("allow_map_transition", False), False)
    # max_retries counts retries after the first attempt per waypoint.
    # auto_path is always strict: when retry budget is hit we reset and keep
    # trying. Recovery events (leader death / party wipe / party defeated)
    # reset the retry counter for a fresh attempt cycle.
    default_max_retries = 6
    max_retries = max(
        1,
        parse_step_int(
            ctx.step.get("max_retries", default_max_retries),
            default_max_retries,
        ),
    )

    add_auto_path_state(
        ctx.bot,
        points=points,
        name=str(name),
        pause_on_combat=pause_on_combat,
        pause_on_danger_was_active=pause_on_danger_was_active,
        arrival_tolerance=arrival_tolerance,
        retry_delay_ms=retry_delay_ms,
        allow_map_transition=allow_map_transition,
        max_retries=max_retries,
        debug_log=lambda message: debug_log_recipe(ctx, message),
        log=lambda message: log_recipe(ctx, message),
    )

    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_delayed(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"AutoPathDelayed {ctx.step_idx + 1}")
    delay_ms = int(ctx.step.get("delay_ms", 35000))
    _add_pre_movement_loot_wait(ctx, str(name))
    add_auto_path_delayed_state(ctx.bot, points=points, name=str(name), delay_ms=delay_ms)
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_until_enemy(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    points = [tuple(p) for p in ctx.step["points"]]
    if not points:
        wait_after_step(ctx.bot, ctx.step)
        return

    name = str(ctx.step.get("name", f"AutoPathUntilEnemy {ctx.step_idx + 1}") or f"AutoPathUntilEnemy {ctx.step_idx + 1}")
    max_dist = parse_step_float(ctx.step.get("max_dist", Range.Compass.value), Range.Compass.value)
    include_dead = parse_step_bool(ctx.step.get("include_dead", False), False)
    set_target = parse_step_bool(ctx.step.get("set_target", False), False)
    point_wait_ms = max(0, parse_step_int(ctx.step.get("point_wait_ms", 0), 0))
    lap_wait_ms = max(0, parse_step_int(ctx.step.get("lap_wait_ms", 0), 0))
    max_laps = max(0, parse_step_int(ctx.step.get("max_laps", 0), 0))
    timeout_ms = max(0, parse_step_int(ctx.step.get("timeout_ms", 0), 0))

    _add_pre_movement_loot_wait(ctx, name)
    add_patrol_until_enemy_state(
        ctx.bot,
        points=points,
        enemy_resolver=_enemy_resolver_for_patrol(ctx, max_dist, include_dead),
        name=name,
        set_target=set_target,
        point_wait_ms=point_wait_ms,
        lap_wait_ms=lap_wait_ms,
        max_laps=max_laps,
        timeout_ms=timeout_ms,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_till_timeout(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    if not points:
        wait_after_step(ctx.bot, ctx.step)
        return

    name = str(ctx.step.get("name", f"AutoPathTillTimeout {ctx.step_idx + 1}") or f"AutoPathTillTimeout {ctx.step_idx + 1}")
    timeout_ms = max(0, parse_step_int(ctx.step.get("timeout_ms", 0), 0))
    point_wait_ms = max(0, parse_step_int(ctx.step.get("point_wait_ms", 0), 0))
    lap_wait_ms = max(0, parse_step_int(ctx.step.get("lap_wait_ms", 0), 0))

    _add_pre_movement_loot_wait(ctx, name)
    add_auto_path_till_timeout_state(
        ctx.bot,
        points=points,
        name=name,
        timeout_ms=timeout_ms,
        point_wait_ms=point_wait_ms,
        lap_wait_ms=lap_wait_ms,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


add_pre_movement_loot_wait = _add_pre_movement_loot_wait
