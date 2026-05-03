"""
Reusable Botting pathing state helpers.

These helpers operate on Botting-style runtime objects, plain parameters, and
callables supplied by adapter layers.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable, Iterable

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_movement import cutscene_active


LogFn = Callable[[str], None]
EnemyResolver = Callable[[], int | None]


def _noop_log(_message: str) -> None:
    return


def add_pre_movement_loot_wait_state(
    bot,
    *,
    step_name: str,
    enabled: bool = True,
    timeout_ms: int = 30_000,
    poll_ms: int = 300,
    loot_range: float = 1_250.0,
    loot_wait_required: Callable[..., bool] | None = None,
) -> None:
    if not enabled or loot_wait_required is None:
        return

    def _wait_for_party_loot():
        from Py4GWCoreLib import Routines

        if timeout_ms <= 0:
            return

        deadline = monotonic() + (max(0, int(timeout_ms)) / 1000.0)
        while monotonic() < deadline and loot_wait_required(search_range=float(loot_range), bot=bot):
            if cutscene_active():
                return
            yield from Routines.Yield.wait(max(50, int(poll_ms)))

    bot.States.AddCustomState(_wait_for_party_loot, f"{step_name}: Wait Party Loot")


def add_path_to_target_state(
    bot,
    *,
    target_resolver: Callable[[], int | None],
    max_dist: float,
    tolerance: float = 150.0,
    required: bool = True,
    name: str = "Path To Target",
) -> bool:
    from Py4GWCoreLib import Agent, Player, Range, Utils

    max_distance = float(max_dist if max_dist > 0 else Range.Compass.value)
    arrival_tolerance = float(tolerance if tolerance > 0 else 150.0)

    def _enqueue_path_to_target():
        px, py = Player.GetXY()
        target_agent_id = target_resolver()
        if target_agent_id is None:
            return

        tx, ty = Agent.GetXY(target_agent_id)
        distance = Utils.Distance((px, py), (tx, ty))

        def _target_invalid(agent_id: int = target_agent_id) -> bool:
            if not Agent.IsValid(agent_id):
                return True
            if not Agent.IsAlive(agent_id):
                return True
            cx, cy = Agent.GetXY(agent_id)
            return Utils.Distance(Player.GetXY(), (cx, cy)) <= arrival_tolerance

        Player.ChangeTarget(target_agent_id)
        yield from bot.Move._coro_xy(tx, ty, name, forced_timeout=max(3000, int(distance * 4)))
        if cutscene_active():
            return
        yield from bot.Wait._coro_until_condition(_target_invalid, duration=100)

    if required or target_resolver() is not None:
        bot.States.AddCustomState(_enqueue_path_to_target, str(name))
        return True
    return False


def add_auto_path_state(
    bot,
    *,
    points: Iterable[tuple[float, float]],
    name: str,
    pause_on_combat: bool,
    pause_on_danger_was_active: bool,
    arrival_tolerance: float,
    retry_delay_ms: int,
    allow_map_transition: bool,
    max_retries: int,
    debug_log: LogFn | None = None,
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import Agent, GLOBAL_CACHE, Map, Player, Routines, Utils

    path_points = [(float(x), float(y)) for x, y in points]
    debug_log_fn = debug_log or _noop_log
    log_fn = log or _noop_log

    def _is_player_dead() -> bool:
        try:
            player_id = int(Player.GetAgentID() or 0)
            return bool(player_id and Agent.IsDead(player_id))
        except Exception:
            return False

    def _recovery_blocking() -> bool:
        try:
            return bool(_is_player_dead() or Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())
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
            if cutscene_active() or not Routines.Checks.Map.MapValid() or Map.IsMapLoading():
                return True
        except Exception:
            return True
        return _map_signature() != map_signature_at_start

    def _run_auto_path():
        map_transition_logged = False
        for point_i, (target_x, target_y) in enumerate(path_points):
            if cutscene_active():
                return
            attempts = 0
            while True:
                if cutscene_active():
                    return
                recovery_waited = False
                while _recovery_blocking():
                    if cutscene_active():
                        return
                    recovery_waited = True
                    yield from bot.Wait._coro_for_time(max(50, int(retry_delay_ms)))
                if recovery_waited and attempts > 0:
                    debug_log_fn(
                        f"{name}: recovery detected, resetting retries for waypoint {point_i + 1}/{len(path_points)}."
                    )
                    attempts = 0

                attempts += 1
                point_step_name = f"{name} [{point_i + 1}/{len(path_points)}]"
                movement_ok = yield from bot.Move._coro_xy(
                    target_x,
                    target_y,
                    step_name=point_step_name,
                    fail_on_unmanaged=False,
                )
                if cutscene_active():
                    return

                if not movement_ok and _map_transition_detected():
                    return

                if _map_transition_detected():
                    if allow_map_transition or cutscene_active():
                        return
                    if not map_transition_logged:
                        log_fn(
                            f"{name}: map transition detected during auto_path; "
                            "holding step until recovery/map restore to avoid stale path advance."
                        )
                        map_transition_logged = True
                    while _map_transition_detected():
                        if cutscene_active():
                            return
                        yield from bot.Wait._coro_for_time(max(50, int(retry_delay_ms)))
                    attempts = 0
                    continue

                distance = _distance_to_target(target_x, target_y)
                if distance <= float(arrival_tolerance):
                    break

                if max_retries > 0 and attempts > max_retries:
                    log_fn(
                        f"{name}: waypoint {point_i + 1}/{len(path_points)} not reached after {attempts} attempts "
                        f"(dist={distance:.0f}, tol={float(arrival_tolerance):.0f}); resetting retry cycle."
                    )
                    attempts = 0
                    yield from bot.Wait._coro_for_time(max(50, int(retry_delay_ms)))
                    continue

                debug_log_fn(
                    f"{name}: retrying waypoint {point_i + 1}/{len(path_points)} "
                    f"(attempt={attempts}, dist={distance:.0f}, tol={float(arrival_tolerance):.0f})"
                )
                yield from bot.Wait._coro_for_time(max(50, int(retry_delay_ms)))

    if pause_on_combat:
        bot.States.AddCustomState(
            lambda: bot.Properties.ApplyNow("pause_on_danger", "active", True),
            f"{name}: Enable Pause On Combat",
        )

    bot.States.AddCustomState(_run_auto_path, str(name))

    if pause_on_combat:
        bot.States.AddCustomState(
            lambda was_active=bool(pause_on_danger_was_active): bot.Properties.ApplyNow(
                "pause_on_danger", "active", was_active
            ),
            f"{name}: Restore Pause On Combat",
        )


def add_auto_path_delayed_state(
    bot,
    *,
    points: Iterable[tuple[float, float]],
    name: str,
    delay_ms: int,
) -> None:
    path_points = [(float(x), float(y)) for x, y in points]
    delay = max(0, int(delay_ms))

    def _run_delayed_path():
        for point_i, (x, y) in enumerate(path_points):
            if cutscene_active():
                return
            step_name = f"{name} [{point_i + 1}/{len(path_points)}]"
            yield from bot.Move._coro_xy(float(x), float(y), step_name=step_name)
            if cutscene_active():
                return
            if point_i < len(path_points) - 1 and delay > 0:
                yield from bot.Wait._coro_for_time(delay)

    bot.States.AddCustomState(_run_delayed_path, str(name))


def add_patrol_until_enemy_state(
    bot,
    *,
    points: Iterable[tuple[float, float]],
    enemy_resolver: EnemyResolver,
    name: str,
    set_target: bool = False,
    point_wait_ms: int = 0,
    lap_wait_ms: int = 0,
    max_laps: int = 0,
    timeout_ms: int = 0,
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import Player

    path_points = [(float(x), float(y)) for x, y in points]
    log_fn = log or _noop_log

    def _patrol_until_enemy():
        started_at = monotonic()
        completed_laps = 0

        while True:
            if cutscene_active():
                return
            detected_enemy = enemy_resolver()
            if detected_enemy is not None:
                if set_target:
                    Player.ChangeTarget(int(detected_enemy))
                return
            if timeout_ms > 0 and (monotonic() - started_at) * 1000.0 >= timeout_ms:
                log_fn(f"{name}: timeout reached without detecting enemies.")
                return
            if max_laps > 0 and completed_laps >= max_laps:
                log_fn(f"{name}: max_laps reached without detecting enemies.")
                return

            for point_idx, (x, y) in enumerate(path_points):
                yield from bot.Move._coro_xy(
                    float(x),
                    float(y),
                    f"{name} [{completed_laps + 1}.{point_idx + 1}]",
                    fail_on_unmanaged=False,
                )
                if cutscene_active():
                    return
                detected_enemy = enemy_resolver()
                if detected_enemy is not None:
                    if set_target:
                        Player.ChangeTarget(int(detected_enemy))
                    return
                if point_wait_ms > 0:
                    yield from bot.Wait._coro_for_time(int(point_wait_ms))

            completed_laps += 1
            if lap_wait_ms > 0:
                yield from bot.Wait._coro_for_time(int(lap_wait_ms))

    bot.States.AddCustomState(_patrol_until_enemy, str(name))


def add_auto_path_till_timeout_state(
    bot,
    *,
    points: Iterable[tuple[float, float]],
    name: str,
    timeout_ms: int,
    point_wait_ms: int = 0,
    lap_wait_ms: int = 0,
    log: LogFn | None = None,
) -> None:
    path_points = [(float(x), float(y)) for x, y in points]
    log_fn = log or _noop_log

    def _run_until_timeout():
        if timeout_ms <= 0:
            log_fn(f"{name}: timeout_ms <= 0, skipping.")
            return

        started_at = monotonic()
        lap_idx = 0
        while True:
            if cutscene_active():
                return
            elapsed_ms = (monotonic() - started_at) * 1000.0
            if elapsed_ms >= timeout_ms:
                return

            for point_idx, (x, y) in enumerate(path_points):
                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return
                remaining_ms = max(1, int(timeout_ms - elapsed_ms))
                yield from bot.Move._coro_xy(
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
                    wait_ms = min(int(point_wait_ms), max(0, int(timeout_ms - elapsed_ms)))
                    if wait_ms > 0:
                        yield from bot.Wait._coro_for_time(wait_ms)

            lap_idx += 1
            if lap_wait_ms > 0:
                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return
                wait_ms = min(int(lap_wait_ms), max(0, int(timeout_ms - elapsed_ms)))
                if wait_ms > 0:
                    yield from bot.Wait._coro_for_time(wait_ms)

    bot.States.AddCustomState(_run_until_timeout, str(name))
