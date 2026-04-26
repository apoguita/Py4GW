"""
actions_movement_pathing module

This module provides pathing-oriented modular movement step handlers.
"""
from __future__ import annotations

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

    def _wait_for_party_loot():
        from time import monotonic

        from Py4GWCoreLib import Routines

        if wait_timeout_ms <= 0:
            return

        deadline = monotonic() + (wait_timeout_ms / 1000.0)
        while monotonic() < deadline and party_loot_wait_required(
            search_range=loot_range,
            bot=ctx.bot,
        ):
            if cutscene_active():
                return
            yield from Routines.Yield.wait(poll_ms)

    ctx.bot.States.AddCustomState(_wait_for_party_loot, f"{step_name}: Wait Party Loot")


def handle_auto_path(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, GLOBAL_CACHE, Map, Player, Routines, Utils

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

    def _is_player_dead() -> bool:
        try:
            player_id = int(Player.GetAgentID() or 0)
            return bool(player_id and Agent.IsDead(player_id))
        except Exception:
            return False

    def _recovery_blocking() -> bool:
        try:
            if _is_player_dead():
                return True
            if Routines.Checks.Party.IsPartyWiped():
                return True
            if GLOBAL_CACHE.Party.IsPartyDefeated():
                return True
            return False
        except Exception:
            return _is_player_dead()

    def _distance_to_target(target_x: float, target_y: float) -> float:
        try:
            px, py = Player.GetXY()
            return float(Utils.Distance((float(px), float(py)), (float(target_x), float(target_y))))
        except Exception:
            return float("inf")

    def _map_signature() -> tuple[int, int, int, int]:
        try:
            region = Map.GetRegion()
            language = Map.GetLanguage()
            return (
                int(Map.GetMapID() or 0),
                int(region[0] if isinstance(region, tuple) and region else 0),
                int(Map.GetDistrict() or 0),
                int(language[0] if isinstance(language, tuple) and language else 0),
            )
        except Exception:
            return (0, 0, 0, 0)

    map_signature_at_start = _map_signature()

    def _map_transition_detected() -> bool:
        try:
            if Map.IsInCinematic() or not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
                return True
        except Exception:
            return True
        return _map_signature() != map_signature_at_start

    def _run_auto_path():
        map_transition_logged = False
        for point_i, (x, y) in enumerate(points):
            if cutscene_active():
                return
            target_x = float(x)
            target_y = float(y)
            attempts = 0

            while True:
                if cutscene_active():
                    return
                recovery_waited = False
                while _recovery_blocking():
                    if cutscene_active():
                        return
                    recovery_waited = True
                    yield from ctx.bot.Wait._coro_for_time(retry_delay_ms)
                if recovery_waited and attempts > 0:
                    debug_log_recipe(
                        ctx,
                        (
                            f"{name}: recovery detected, resetting retries for "
                            f"waypoint {point_i + 1}/{len(points)}."
                        ),
                    )
                    attempts = 0

                attempts += 1
                point_step_name = f"{name} [{point_i + 1}/{len(points)}]"
                yield from ctx.bot.Move._coro_xy(
                    target_x,
                    target_y,
                    step_name=point_step_name,
                    fail_on_unmanaged=False,
                )

                if cutscene_active():
                    return

                if _map_transition_detected():
                    if allow_map_transition:
                        return

                    if not map_transition_logged:
                        log_recipe(
                            ctx,
                            (
                                f"{name}: map transition detected during auto_path; "
                                "holding step until recovery/map restore to avoid stale path advance."
                            ),
                        )
                        map_transition_logged = True

                    while _map_transition_detected():
                        if cutscene_active():
                            return
                        yield from ctx.bot.Wait._coro_for_time(retry_delay_ms)
                    attempts = 0
                    continue

                distance = _distance_to_target(target_x, target_y)
                if distance <= arrival_tolerance:
                    break

                retry_budget_exhausted = max_retries > 0 and attempts > max_retries
                if retry_budget_exhausted:
                    log_recipe(
                        ctx,
                        (
                            f"{name}: waypoint {point_i + 1}/{len(points)} not reached "
                            f"after {attempts} attempts (dist={distance:.0f}, tol={arrival_tolerance:.0f}); "
                            f"resetting retry cycle."
                        ),
                    )
                    attempts = 0
                    yield from ctx.bot.Wait._coro_for_time(retry_delay_ms)
                    continue

                debug_log_recipe(
                    ctx,
                    (
                        f"{name}: retrying waypoint {point_i + 1}/{len(points)} "
                        f"(attempt={attempts}, dist={distance:.0f}, tol={arrival_tolerance:.0f})"
                    ),
                )
                yield from ctx.bot.Wait._coro_for_time(retry_delay_ms)
                if cutscene_active():
                    return

    if pause_on_combat:
        # Enable before movement executes (FSM runtime), not during step registration.
        ctx.bot.States.AddCustomState(
            lambda: ctx.bot.Properties.ApplyNow("pause_on_danger", "active", True),
            f"{name}: Enable Pause On Combat",
        )

    ctx.bot.States.AddCustomState(_run_auto_path, str(name))

    if pause_on_combat:
        # Restore previous setting after movement completes.
        ctx.bot.States.AddCustomState(
            lambda was_active=pause_on_danger_was_active: ctx.bot.Properties.ApplyNow(
                "pause_on_danger", "active", was_active
            ),
            f"{name}: Restore Pause On Combat",
        )

    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_delayed(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"AutoPathDelayed {ctx.step_idx + 1}")
    delay_ms = int(ctx.step.get("delay_ms", 35000))
    _add_pre_movement_loot_wait(ctx, str(name))
    if delay_ms < 0:
        delay_ms = 0

    def _run_delayed_path():
        for point_i, (x, y) in enumerate(points):
            if cutscene_active():
                return
            step_name = f"{name} [{point_i + 1}/{len(points)}]"
            yield from ctx.bot.Move._coro_xy(float(x), float(y), step_name=step_name)
            if cutscene_active():
                return
            if point_i < len(points) - 1 and delay_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(delay_ms)

    ctx.bot.States.AddCustomState(_run_delayed_path, str(name))
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_until_enemy(ctx: StepContext) -> None:
    from time import monotonic

    from Py4GWCoreLib import Agent, AgentArray, Player, Range

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

    def _patrol_until_enemy():
        started_at = monotonic()
        completed_laps = 0

        while True:
            if cutscene_active():
                return
            detected_enemy = _resolve_detected_enemy()
            if detected_enemy is not None:
                if set_target:
                    Player.ChangeTarget(int(detected_enemy))
                return

            if timeout_ms > 0 and (monotonic() - started_at) * 1000.0 >= timeout_ms:
                log_recipe(ctx, f"{name}: timeout reached without detecting enemies.")
                return

            if max_laps > 0 and completed_laps >= max_laps:
                log_recipe(ctx, f"{name}: max_laps reached without detecting enemies.")
                return

            for point_idx, (x, y) in enumerate(points):
                yield from ctx.bot.Move._coro_xy(
                    float(x),
                    float(y),
                    f"{name} [{completed_laps + 1}.{point_idx + 1}]",
                    fail_on_unmanaged=False,
                )
                if cutscene_active():
                    return

                detected_enemy = _resolve_detected_enemy()
                if detected_enemy is not None:
                    if set_target:
                        Player.ChangeTarget(int(detected_enemy))
                    return

                if point_wait_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(point_wait_ms)
                    if cutscene_active():
                        return

            completed_laps += 1
            if lap_wait_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(lap_wait_ms)
                if cutscene_active():
                    return

    _add_pre_movement_loot_wait(ctx, name)
    ctx.bot.States.AddCustomState(_patrol_until_enemy, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path_till_timeout(ctx: StepContext) -> None:
    from time import monotonic

    points = [tuple(p) for p in ctx.step["points"]]
    if not points:
        wait_after_step(ctx.bot, ctx.step)
        return

    name = str(ctx.step.get("name", f"AutoPathTillTimeout {ctx.step_idx + 1}") or f"AutoPathTillTimeout {ctx.step_idx + 1}")
    timeout_ms = max(0, parse_step_int(ctx.step.get("timeout_ms", 0), 0))
    point_wait_ms = max(0, parse_step_int(ctx.step.get("point_wait_ms", 0), 0))
    lap_wait_ms = max(0, parse_step_int(ctx.step.get("lap_wait_ms", 0), 0))

    def _run_until_timeout():
        if timeout_ms <= 0:
            log_recipe(ctx, f"{name}: timeout_ms <= 0, skipping.")
            return

        started_at = monotonic()
        lap_idx = 0

        while True:
            if cutscene_active():
                return
            elapsed_ms = (monotonic() - started_at) * 1000.0
            if elapsed_ms >= timeout_ms:
                return

            for point_idx, (x, y) in enumerate(points):
                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return

                remaining_ms = max(1, int(timeout_ms - elapsed_ms))
                yield from ctx.bot.Move._coro_xy(
                    float(x),
                    float(y),
                    f"{name} [{lap_idx + 1}.{point_idx + 1}]",
                    forced_timeout=remaining_ms,
                    fail_on_unmanaged=False,
                )
                if cutscene_active():
                    return

                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return

                if point_wait_ms > 0:
                    wait_ms = min(point_wait_ms, max(0, int(timeout_ms - elapsed_ms)))
                    if wait_ms > 0:
                        yield from ctx.bot.Wait._coro_for_time(wait_ms)
                        if cutscene_active():
                            return

            lap_idx += 1
            if lap_wait_ms > 0:
                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return
                wait_ms = min(lap_wait_ms, max(0, int(timeout_ms - elapsed_ms)))
                if wait_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(wait_ms)
                    if cutscene_active():
                        return

    _add_pre_movement_loot_wait(ctx, name)
    ctx.bot.States.AddCustomState(_run_until_timeout, name)
    wait_after_step(ctx.bot, ctx.step)


add_pre_movement_loot_wait = _add_pre_movement_loot_wait
