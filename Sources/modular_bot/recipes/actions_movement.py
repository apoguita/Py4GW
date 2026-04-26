from __future__ import annotations

import random
from typing import Callable

from .actions_party import apply_hero_ai_combat_state, apply_auto_looting_state
from .combat_engine import (
    ENGINE_HERO_AI,
    is_party_looting_enabled,
    outbound_messages_done,
    party_loot_wait_required,
    resolve_engine_for_bot,
    send_multibox_command,
)
from .step_context import StepContext
from .step_selectors import resolve_enemy_agent_id_from_step
from .step_utils import (
    debug_log_recipe,
    log_recipe,
    parse_step_bool,
    parse_step_float,
    parse_step_int,
    parse_step_point,
    wait_after_step,
)

_PARTY_BACKEND_HERO_AI = "hero_ai"
_PARTY_BACKEND_SHARED = "shared"


def _resolve_party_backend() -> str:
    """Choose party-control backend from currently enabled widgets."""
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    widget_handler = get_widget_handler()
    hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))

    if hero_ai_enabled:
        return _PARTY_BACKEND_HERO_AI
    return _PARTY_BACKEND_SHARED


def _current_hero_ai_combat_enabled(ctx: StepContext) -> bool:
    engine = resolve_engine_for_bot(ctx.bot)
    if engine == ENGINE_HERO_AI:
        try:
            from Py4GWCoreLib import GLOBAL_CACHE, Player

            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(Player.GetAccountEmail())
            if options is not None:
                return bool(getattr(options, "Combat", False))
        except Exception:
            pass

        if ctx.bot.Properties.exists("hero_ai"):
            return bool(ctx.bot.Properties.IsActive("hero_ai"))
        return False

    if ctx.bot.Properties.exists("hero_ai"):
        return bool(ctx.bot.Properties.IsActive("hero_ai"))
    return False


def _current_auto_looting_enabled(ctx: StepContext) -> bool:
    engine = resolve_engine_for_bot(ctx.bot)
    if engine == ENGINE_HERO_AI:
        try:
            return bool(is_party_looting_enabled(bot=ctx.bot, preferred_engine=engine))
        except Exception:
            return False

    if ctx.bot.Properties.exists("auto_loot"):
        return bool(ctx.bot.Properties.IsActive("auto_loot"))
    return False


def _wrap_with_auto_state_guard(ctx: StepContext, action_factory: Callable):
    def _guarded_action():
        looting_was_enabled = _current_auto_looting_enabled(ctx)
        combat_was_enabled = _current_hero_ai_combat_enabled(ctx)
        pause_on_danger_exists = bool(ctx.bot.Properties.exists("pause_on_danger"))
        pause_on_danger_was_active = (
            bool(ctx.bot.Properties.IsActive("pause_on_danger")) if pause_on_danger_exists else False
        )

        if looting_was_enabled:
            apply_auto_looting_state(ctx.bot, False)
        if combat_was_enabled:
            apply_hero_ai_combat_state(ctx.bot, False)

        try:
            yield from action_factory()
        finally:
            if looting_was_enabled:
                apply_auto_looting_state(ctx.bot, True)
            if combat_was_enabled:
                apply_hero_ai_combat_state(ctx.bot, True)
            if pause_on_danger_exists:
                ctx.bot.Properties.ApplyNow("pause_on_danger", "active", pause_on_danger_was_active)

    return _guarded_action


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
            yield from Routines.Yield.wait(poll_ms)

    ctx.bot.States.AddCustomState(_wait_for_party_loot, f"{step_name}: Wait Party Loot")


def handle_path(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"Path {ctx.step_idx + 1}")
    _add_pre_movement_loot_wait(ctx, str(name))
    ctx.bot.Move.FollowAutoPath(points, step_name=name)
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player, Routines, Utils

    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"AutoPath {ctx.step_idx + 1}")
    _add_pre_movement_loot_wait(ctx, str(name))
    pause_on_combat = parse_step_bool(ctx.step.get("pause_on_combat", False), False)
    pause_on_danger_was_active = bool(ctx.bot.Properties.IsActive("pause_on_danger"))
    default_tolerance = float(ctx.bot.config.config_properties.movement_tolerance.get("value") or 150.0)
    arrival_tolerance = max(25.0, parse_step_float(ctx.step.get("arrival_tolerance", ctx.step.get("tolerance", default_tolerance)), default_tolerance))
    retry_delay_ms = max(50, parse_step_int(ctx.step.get("retry_delay_ms", 350), 350))
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

    def _run_auto_path():
        for point_i, (x, y) in enumerate(points):
            target_x = float(x)
            target_y = float(y)
            attempts = 0

            while True:
                recovery_waited = False
                while _recovery_blocking():
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
                yield from ctx.bot.Move._coro_xy(target_x, target_y, step_name=point_step_name)

                if not Routines.Checks.Map.MapValid():
                    return

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
    for point_i, (x, y) in enumerate(points):
        step_name = f"{name} [{point_i + 1}/{len(points)}]"
        ctx.bot.Move.XY(x, y, step_name=step_name)
        if point_i < len(points) - 1 and delay_ms > 0:
            ctx.bot.Wait.ForTime(delay_ms)
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
                yield from ctx.bot.Move._coro_xy(float(x), float(y), f"{name} [{completed_laps + 1}.{point_idx + 1}]")

                detected_enemy = _resolve_detected_enemy()
                if detected_enemy is not None:
                    if set_target:
                        Player.ChangeTarget(int(detected_enemy))
                    return

                if point_wait_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(point_wait_ms)

            completed_laps += 1
            if lap_wait_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(lap_wait_ms)

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
                )

                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return

                if point_wait_ms > 0:
                    wait_ms = min(point_wait_ms, max(0, int(timeout_ms - elapsed_ms)))
                    if wait_ms > 0:
                        yield from ctx.bot.Wait._coro_for_time(wait_ms)

            lap_idx += 1
            if lap_wait_ms > 0:
                elapsed_ms = (monotonic() - started_at) * 1000.0
                if elapsed_ms >= timeout_ms:
                    return
                wait_ms = min(lap_wait_ms, max(0, int(timeout_ms - elapsed_ms)))
                if wait_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(wait_ms)

    _add_pre_movement_loot_wait(ctx, name)
    ctx.bot.States.AddCustomState(_run_until_timeout, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_wait(ctx: StepContext) -> None:
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_out_of_combat(ctx: StepContext) -> None:
    ctx.bot.Wait.UntilOutOfCombat()
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_load(ctx: StepContext) -> None:
    map_id = int(ctx.step.get("map_id", ctx.step.get("target_map_id", 0)) or 0)
    ctx.bot.Wait.ForMapLoad(target_map_id=map_id)
    wait_after_step(ctx.bot, ctx.step)


def handle_move(ctx: StepContext) -> None:
    coords = parse_step_point(ctx.step)
    if coords is None:
        log_recipe(ctx, f"move invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
        wait_after_step(ctx.bot, ctx.step)
        return
    x, y = coords
    name = ctx.step.get("name", "")
    _add_pre_movement_loot_wait(ctx, str(name or f"Move {ctx.step_idx + 1}"))
    ctx.bot.Move.XY(x, y, step_name=name)
    wait_after_step(ctx.bot, ctx.step)


def handle_nudge_move(ctx: StepContext) -> None:
    from Py4GWCoreLib import Player

    coords = parse_step_point(ctx.step)
    if coords is None:
        log_recipe(ctx, f"nudge_move invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
        wait_after_step(ctx.bot, ctx.step)
        return
    x, y = coords
    name = str(ctx.step.get("name", f"Nudge {ctx.step_idx + 1}") or f"Nudge {ctx.step_idx + 1}")
    pulses = max(1, parse_step_int(ctx.step.get("pulses", 1), 1))
    pulse_ms = max(0, parse_step_int(ctx.step.get("pulse_ms", ctx.step.get("move_ms", 250)), 250))

    def _nudge():
        for pulse_idx in range(pulses):
            Player.Move(x, y)
            if pulse_ms > 0 and pulse_idx < (pulses - 1):
                yield from ctx.bot.Wait._coro_for_time(pulse_ms)

    ctx.bot.States.AddCustomState(_nudge, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_path_to_target(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, Player, Range, Utils

    max_dist = parse_step_float(ctx.step.get("max_dist", Range.Compass.value), Range.Compass.value)
    tolerance = parse_step_float(ctx.step.get("tolerance", 150.0), 150.0)
    required = parse_step_bool(ctx.step.get("required", True), True)
    step_name = ctx.step.get("name", "Path To Target")
    _add_pre_movement_loot_wait(ctx, str(step_name))

    if max_dist <= 0:
        max_dist = Range.Compass.value
    if tolerance <= 0:
        tolerance = 150.0

    def _enqueue_path_to_target():
        px, py = Player.GetXY()
        target_agent_id = resolve_enemy_agent_id_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            default_max_dist=max_dist,
        )
        if target_agent_id is None:
            if not required:
                wait_after_step(ctx.bot, ctx.step)
            return

        tx, ty = Agent.GetXY(target_agent_id)
        distance = Utils.Distance((px, py), (tx, ty))

        def _target_invalid(agent_id: int = target_agent_id) -> bool:
            if not Agent.IsValid(agent_id):
                return True
            if not Agent.IsAlive(agent_id):
                return True
            cx, cy = Agent.GetXY(agent_id)
            return Utils.Distance(Player.GetXY(), (cx, cy)) <= tolerance

        Player.ChangeTarget(target_agent_id)
        yield from ctx.bot.Move._coro_xy(tx, ty, step_name, forced_timeout=max(3000, int(distance * 4)))
        yield from ctx.bot.Wait._coro_until_condition(_target_invalid, duration=100)

    ctx.bot.States.AddCustomState(_enqueue_path_to_target, step_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_travel(ctx: StepContext) -> None:
    target_map_id = int(ctx.step.get("target_map_id", 0))
    target_map_name = str(ctx.step.get("target_map_name", "") or "")
    leave_party = parse_step_bool(ctx.step.get("leave_party", True), True)
    if leave_party:
        ctx.bot.Party.LeaveParty()
    ctx.bot.Map.Travel(target_map_id=target_map_id, target_map_name=target_map_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_random_travel(ctx: StepContext) -> None:
    from Py4GWCoreLib import Map
    from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
    from Py4GWCoreLib.enums_src.Region_enums import District

    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)
    target_map_name = str(ctx.step.get("target_map_name", "") or "").strip()
    settle_wait_ms = parse_step_int(ctx.step.get("travel_wait_ms", 500), 500)

    if target_map_id <= 0 and target_map_name:
        target_map_id = int(name_to_map_id.get(target_map_name, 0))

    if target_map_id <= 0:
        log_recipe(ctx, f"random_travel skipped: unresolved target map for step {ctx.step_idx + 1}.")
        wait_after_step(ctx.bot, ctx.step)
        return

    leave_party = parse_step_bool(ctx.step.get("leave_party", True), True)
    if leave_party:
        ctx.bot.Party.LeaveParty()

    raw_districts = ctx.step.get("districts", ctx.step.get("allowed_districts"))
    if raw_districts is None:
        raw_districts = [
            District.EuropeItalian.name,
            District.EuropeSpanish.name,
            District.EuropePolish.name,
            District.EuropeRussian.name,
        ]

    allowed_districts: list[int] = []
    for raw_district in raw_districts:
        if isinstance(raw_district, str):
            district_name = raw_district.strip()
            district = District.__members__.get(district_name)
            if district is not None:
                allowed_districts.append(int(district.value))
                continue

        district_value = parse_step_int(raw_district, -1)
        if district_value in District._value2member_map_:
            allowed_districts.append(district_value)

    allowed_districts = [
        district for district in allowed_districts if district not in (District.Current.value, District.Unknown.value)
    ]
    if not allowed_districts:
        allowed_districts = [
            District.EuropeItalian.value,
            District.EuropeSpanish.value,
            District.EuropePolish.value,
            District.EuropeRussian.value,
        ]

    def _travel() -> None:
        district = int(random.choice(allowed_districts))
        Map.TravelToDistrict(target_map_id, district=district)

    ctx.bot.States.AddCustomState(_travel, ctx.step.get("name", f"Random Travel {ctx.step_idx + 1}"))
    if settle_wait_ms > 0:
        ctx.bot.Wait.ForTime(settle_wait_ms)
    ctx.bot.Wait.ForMapLoad(target_map_id=target_map_id)
    wait_after_step(ctx.bot, ctx.step)


def handle_travel_gh(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, Routines, SharedCommandType

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)

    def _run_travel_gh() -> None:
        def _prepare_local_for_gh() -> None:
            if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
                debug_log_recipe(ctx, "travel_gh requested while explorable; resigning to outpost first.")
                if multibox:
                    ctx.bot.Multibox.ResignParty()
                else:
                    ctx.bot.Party.Resign()
                ctx.bot.Wait.UntilOnOutpost()
                ctx.bot.Wait.ForTime(1000)

        def _send_local_gh_message() -> list[tuple[str, int]]:
            sender_email = Player.GetAccountEmail()
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                sender_email,
                SharedCommandType.TravelToGuildHall,
                (0, 0, 0, 0),
            )
            return [(sender_email, int(message_index))]

        _prepare_local_for_gh()
        if Map.IsGuildHall():
            debug_log_recipe(ctx, "Already in Guild Hall; skipping TravelGH.")
            return

        backend = _resolve_party_backend()
        if multibox and backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(ctx, "travel_gh: HeroAI backend active, dispatching alts + local self-message.")
            sent_refs = send_multibox_command(SharedCommandType.TravelToGuildHall)
            sent_refs.extend(_send_local_gh_message())
            ctx.bot.Wait.UntilCondition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )
        elif multibox:
            debug_log_recipe(ctx, "travel_gh: ambiguous/no engine widget state, dispatching shared GH travel command.")
            sent_refs = send_multibox_command(SharedCommandType.TravelToGuildHall)
            sent_refs.extend(_send_local_gh_message())
            ctx.bot.Wait.UntilCondition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )
        else:
            local_refs = _send_local_gh_message()
            ctx.bot.Wait.UntilCondition(
                lambda refs=local_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )

    ctx.bot.States.AddCustomState(_run_travel_gh, ctx.step.get("name", f"Travel GH {ctx.step_idx + 1}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_leave_party(ctx: StepContext) -> None:
    from Py4GWCoreLib import SharedCommandType

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    def _run_leave_party() -> None:
        sent_refs: list[tuple[str, int]] = []
        used_cb_scheduler = False

        backend = _resolve_party_backend()
        if multibox:
            if backend == _PARTY_BACKEND_HERO_AI:
                debug_log_recipe(ctx, "leave_party: HeroAI backend active, dispatching shared leave command.")
            elif backend == _PARTY_BACKEND_SHARED:
                debug_log_recipe(ctx, "leave_party: ambiguous/no engine widget state, dispatching shared leave command.")
            if not used_cb_scheduler:
                sent_refs = send_multibox_command(SharedCommandType.LeaveParty)
            ctx.bot.Party.LeaveParty()
            if sent_refs:
                ctx.bot.Wait.UntilCondition(
                    lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.LeaveParty),
                    duration=100,
                )
        else:
            ctx.bot.Party.LeaveParty()

    ctx.bot.States.AddCustomState(_run_leave_party, ctx.step.get("name", f"Leave Party {ctx.step_idx + 1}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_exit_map(ctx: StepContext) -> None:
    coords = parse_step_point(ctx.step)
    if coords is None:
        log_recipe(ctx, f"exit_map invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
        wait_after_step(ctx.bot, ctx.step)
        return
    x, y = coords
    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)
    target_map_name = str(ctx.step.get("target_map_name", "") or "").strip()
    step_name = str(ctx.step.get("name", "Exit Map") or "Exit Map")
    anchor_state_name = f"{step_name}: Post-Map Anchor"
    suppress_recovery_ms = max(0, parse_step_int(ctx.step.get("suppress_recovery_ms", 10_000), 10_000))
    suppress_recovery_events = max(0, parse_step_int(ctx.step.get("suppress_recovery_events", 6), 6))

    def _exit_map_core():
        yield from ctx.bot.Move._coro_xy_and_exit_map(
            x,
            y,
            target_map_id=target_map_id,
            step_name=step_name,
        )

    if (target_map_id > 0 or target_map_name) and suppress_recovery_ms > 0:
        def _suppress_transition_recovery(
            _ms: int = suppress_recovery_ms,
            _events: int = suppress_recovery_events,
        ) -> None:
            owner = getattr(ctx.bot, "_modular_owner", None)
            if owner is None or not hasattr(owner, "suppress_recovery_for"):
                return
            owner.suppress_recovery_for(ms=_ms, max_events=_events)

        ctx.bot.States.AddCustomState(_suppress_transition_recovery, f"{step_name}: Suppress Recovery")

    ctx.bot.States.AddCustomState(_wrap_with_auto_state_guard(ctx, _exit_map_core), step_name)

    if target_map_id > 0 or target_map_name:
        # Ensure we are fully in the target map before continuing any post-transition logic.
        ctx.bot.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

    def _set_post_exit_anchor(_anchor_state: str = anchor_state_name) -> None:
        owner = getattr(ctx.bot, "_modular_owner", None)
        if owner is None or not hasattr(owner, "set_anchor"):
            return
        owner.set_anchor(_anchor_state)

    # Refresh runtime recovery anchor after each map transition so recovery
    # cannot fall back to a stale pre-transition anchor.
    ctx.bot.States.AddCustomState(_set_post_exit_anchor, anchor_state_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_follow_model(ctx: StepContext) -> None:
    from time import monotonic

    model_id = int(str(ctx.step["model_id"]), 0)
    follow_range = float(ctx.step.get("follow_range", ctx.step.get("range", 600)))
    timeout_ms = int(ctx.step.get("timeout_ms", 0))

    if timeout_ms > 0:
        start = monotonic()
        ctx.bot.Move.FollowModel(
            model_id,
            follow_range,
            exit_condition=lambda _s=start, _t=timeout_ms: (monotonic() - _s) * 1000.0 >= _t,
        )
    else:
        ctx.bot.Move.FollowModel(model_id, follow_range)
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_change(ctx: StepContext) -> None:
    ctx.bot.Wait.ForMapToChange(target_map_id=ctx.step["target_map_id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_enter_challenge(ctx: StepContext) -> None:
    from Py4GWCoreLib import Key, Keystroke, Map

    step_name = str(ctx.step.get("name", "Enter Challenge") or "Enter Challenge")
    delay_ms = parse_step_int(ctx.step.get("delay_ms", ctx.step.get("delay", 2000)), 2000)
    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)

    ctx.bot.States.AddCustomState(lambda: Map.EnterChallenge(), f"{step_name}: Trigger")
    if delay_ms > 0:
        ctx.bot.Wait.ForTime(delay_ms)
    ctx.bot.States.AddCustomState(
        lambda: Keystroke.PressAndRelease(getattr(Key, "Enter").value),
        f"{step_name}: Confirm",
    )
    if target_map_id > 0:
        ctx.bot.Wait.ForMapToChange(target_map_id=target_map_id)
    else:
        ctx.bot.Wait.ForMapToChange()
    wait_after_step(ctx.bot, ctx.step)


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "path": handle_path,
    "auto_path": handle_auto_path,
    "auto_path_delayed": handle_auto_path_delayed,
    "auto_path_until_enemy": handle_auto_path_until_enemy,
    "patrol_until_enemy": handle_auto_path_until_enemy,
    "auto_path_till_timeout": handle_auto_path_till_timeout,
    "auto_path_until_timeout": handle_auto_path_till_timeout,
    "wait": handle_wait,
    "wait_out_of_combat": handle_wait_out_of_combat,
    "wait_map_load": handle_wait_map_load,
    "wait_for_map_load": handle_wait_map_load,
    "move": handle_move,
    "nudge_move": handle_nudge_move,
    "nudge": handle_nudge_move,
    "path_to_target": handle_path_to_target,
    "travel": handle_travel,
    "random_travel": handle_random_travel,
    "travel_gh": handle_travel_gh,
    "leave_party": handle_leave_party,
    "exit_map": handle_exit_map,
    "follow_model": handle_follow_model,
    "wait_map_change": handle_wait_map_change,
    "enter_challenge": handle_enter_challenge,
}
