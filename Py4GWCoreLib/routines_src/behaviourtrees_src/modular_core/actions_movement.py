"""
actions_movement module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

import random
from typing import Callable

from .actions_party_toggles import (
    apply_auto_combat_state,
    apply_auto_looting_state,
    current_auto_combat_enabled,
    current_auto_looting_enabled,
)
from .combat_engine import (
    outbound_messages_done,
    party_loot_wait_required,
    send_multibox_command,
)
from .step_context import StepContext
from .step_selectors import resolve_enemy_agent_id_from_step
from .actions_movement_pathing import (
    add_pre_movement_loot_wait as _add_pre_movement_loot_wait,
    handle_auto_path,
    handle_auto_path_delayed,
    handle_auto_path_till_timeout,
    handle_auto_path_until_enemy,
)
from .step_utils import (
    cutscene_active,
    debug_log_recipe,
    log_recipe,
    parse_step_bool,
    parse_step_float,
    parse_step_int,
    parse_step_point,
    wait_after_step,
)
from .step_registration import modular_step

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


def _wrap_with_auto_state_guard(ctx: StepContext, action_factory: Callable):
    def _guarded_action():
        looting_was_enabled = current_auto_looting_enabled(ctx.bot)
        combat_was_enabled = current_auto_combat_enabled(ctx.bot)
        pause_on_danger_exists = bool(ctx.bot.Properties.exists("pause_on_danger"))
        pause_on_danger_was_active = (
            bool(ctx.bot.Properties.IsActive("pause_on_danger")) if pause_on_danger_exists else False
        )

        if looting_was_enabled:
            apply_auto_looting_state(ctx.bot, False)
        if combat_was_enabled:
            apply_auto_combat_state(ctx.bot, False)

        try:
            yield from action_factory()
        finally:
            if looting_was_enabled:
                apply_auto_looting_state(ctx.bot, True)
            if combat_was_enabled:
                apply_auto_combat_state(ctx.bot, True)
            if pause_on_danger_exists:
                ctx.bot.Properties.ApplyNow("pause_on_danger", "active", pause_on_danger_was_active)

    return _guarded_action


def handle_path(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"Path {ctx.step_idx + 1}")
    _add_pre_movement_loot_wait(ctx, str(name))

    def _run_path():
        for point_i, (x, y) in enumerate(points):
            if cutscene_active():
                return
            step_name = f"{name} [{point_i + 1}/{len(points)}]"
            yield from ctx.bot.Move._coro_xy(float(x), float(y), step_name=step_name)
            if cutscene_active():
                return

    ctx.bot.States.AddCustomState(_run_path, str(name))
    wait_after_step(ctx.bot, ctx.step)


def handle_wait(ctx: StepContext) -> None:
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_out_of_combat(ctx: StepContext) -> None:
    def _wait_out_of_combat():
        from Py4GWCoreLib import Range, Routines

        while Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot):
            if cutscene_active():
                return
            yield from ctx.bot.Wait._coro_for_time(1000)

    ctx.bot.States.AddCustomState(_wait_out_of_combat, ctx.step.get("name", "Wait Out Of Combat"))
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_load(ctx: StepContext) -> None:
    map_id = int(ctx.step.get("map_id", ctx.step.get("target_map_id", 0)) or 0)

    def _wait_map_load():
        if cutscene_active():
            return
        yield from ctx.bot.Wait._coro_for_map_load(target_map_id=map_id)

    ctx.bot.States.AddCustomState(_wait_map_load, ctx.step.get("name", "Wait Map Load"))
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

    def _move():
        if cutscene_active():
            return
        yield from ctx.bot.Move._coro_xy(x, y, step_name=name)

    ctx.bot.States.AddCustomState(_move, str(name or f"Move {ctx.step_idx + 1}"))
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
            if cutscene_active():
                return
            Player.Move(x, y)
            if pulse_ms > 0 and pulse_idx < (pulses - 1):
                yield from ctx.bot.Wait._coro_for_time(pulse_ms)
                if cutscene_active():
                    return

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
        if cutscene_active():
            return
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
    per_account_delay_ms = max(0, parse_step_int(ctx.step.get("per_account_delay_ms", 500), 500))

    def _run_travel_gh():
        def _prepare_local_for_gh() -> None:
            if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
                debug_log_recipe(ctx, "travel_gh requested while explorable; resigning to outpost first.")
                if multibox:
                    ctx.bot.Multibox.ResignParty()
                else:
                    ctx.bot.Party.Resign()
                ctx.bot.Wait.UntilOnOutpost()
                ctx.bot.Wait.ForTime(1000)

        def _send_remote_gh_messages():
            sender_email = Player.GetAccountEmail()
            refs: list[tuple[str, int]] = []
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                account_email = str(getattr(account, "AccountEmail", "") or "")
                if not account_email or account_email == sender_email:
                    continue
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.TravelToGuildHall,
                    (0, 0, 0, 0),
                )
                refs.append((account_email, int(message_index)))
                if per_account_delay_ms > 0:
                    yield from ctx.bot.Wait._coro_for_time(per_account_delay_ms)
            return refs

        def _travel_local_gh():
            if not Map.IsGuildHall():
                yield from ctx.bot.Map._coro_travel_to_gh(wait_time=1000)

        _prepare_local_for_gh()
        if Map.IsGuildHall():
            debug_log_recipe(ctx, "Already in Guild Hall; skipping TravelGH.")
            return

        backend = _resolve_party_backend()
        if multibox and backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(
                ctx,
                f"travel_gh: HeroAI backend active, dispatching shared GH travel command "
                f"(delay={per_account_delay_ms}ms/account).",
            )
            sent_refs = yield from _send_remote_gh_messages()
            yield from _travel_local_gh()
            yield from ctx.bot.Wait._coro_until_condition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )
        elif multibox:
            debug_log_recipe(
                ctx,
                f"travel_gh: no HeroAI widget state, dispatching shared GH travel command "
                f"(delay={per_account_delay_ms}ms/account).",
            )
            sent_refs = yield from _send_remote_gh_messages()
            yield from _travel_local_gh()
            yield from ctx.bot.Wait._coro_until_condition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )
        else:
            yield from _travel_local_gh()

    ctx.bot.States.AddCustomState(_run_travel_gh, ctx.step.get("name", f"Travel GH {ctx.step_idx + 1}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_leave_party(ctx: StepContext) -> None:
    from Py4GWCoreLib import SharedCommandType

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    def _run_leave_party() -> None:
        sent_refs: list[tuple[str, int]] = []

        backend = _resolve_party_backend()
        if multibox:
            if backend == _PARTY_BACKEND_HERO_AI:
                debug_log_recipe(ctx, "leave_party: HeroAI backend active, dispatching shared leave command.")
            elif backend == _PARTY_BACKEND_SHARED:
                debug_log_recipe(ctx, "leave_party: no HeroAI widget state, dispatching shared leave command.")
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
        yield from ctx.bot.Move._coro_xy(x, y, step_name=step_name)
        if cutscene_active():
            return
        if target_map_id > 0 or target_map_name:
            yield from ctx.bot.Wait._coro_for_map_load(
                target_map_id=target_map_id,
                target_map_name=target_map_name,
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

    ctx.bot.States.AddCustomState(_exit_map_core, step_name)

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
            exit_condition=lambda _s=start, _t=timeout_ms: (
                cutscene_active() or (monotonic() - _s) * 1000.0 >= _t
            ),
        )
    else:
        ctx.bot.Move.FollowModel(model_id, follow_range, exit_condition=cutscene_active)
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_change(ctx: StepContext) -> None:
    def _wait_map_change():
        if cutscene_active():
            return
        yield from ctx.bot.Wait._coro_for_map_to_change(target_map_id=ctx.step["target_map_id"])

    ctx.bot.States.AddCustomState(_wait_map_change, ctx.step.get("name", "Wait Map Change"))
    wait_after_step(ctx.bot, ctx.step)


def handle_enter_challenge(ctx: StepContext) -> None:
    from Py4GWCoreLib import Key, Keystroke, Map

    step_name = str(ctx.step.get("name", "Enter Challenge") or "Enter Challenge")
    delay_ms = parse_step_int(ctx.step.get("delay_ms", ctx.step.get("delay", 2000)), 2000)
    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)

    def _enter_challenge():
        if cutscene_active():
            return
        Map.EnterChallenge()
        if delay_ms > 0:
            yield from ctx.bot.Wait._coro_for_time(delay_ms)
        if cutscene_active():
            return
        Keystroke.PressAndRelease(getattr(Key, "Enter").value)
        if cutscene_active():
            return
        if target_map_id > 0:
            yield from ctx.bot.Wait._coro_for_map_to_change(target_map_id=target_map_id)
        else:
            yield from ctx.bot.Wait._coro_for_map_to_change()

    ctx.bot.States.AddCustomState(_enter_challenge, step_name)
    wait_after_step(ctx.bot, ctx.step)


# Decorator-driven step registration bindings.
modular_step(
    step_type="auto_path",
    category="movement",
    allowed_params=(
        "allow_map_transition",
        "arrival_tolerance",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "max_retries",
        "name",
        "pause_on_combat",
        "points",
        "retry_delay_ms",
        "tolerance",
        "wait_for_loot",
    ),
    node_class_name="AutoPathNode",
)(handle_auto_path)
modular_step(
    step_type="auto_path_delayed",
    category="movement",
    allowed_params=(
        "delay_ms",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "name",
        "points",
        "wait_for_loot",
    ),
    node_class_name="AutoPathDelayedNode",
)(handle_auto_path_delayed)
modular_step(
    step_type="auto_path_till_timeout",
    category="movement",
    allowed_params=(
        "lap_wait_ms",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "name",
        "point_wait_ms",
        "points",
        "timeout_ms",
        "wait_for_loot",
    ),
    node_class_name="AutoPathTillTimeoutNode",
)(handle_auto_path_till_timeout)
modular_step(
    step_type="auto_path_until_enemy",
    category="movement",
    allowed_params=(
        "include_dead",
        "lap_wait_ms",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "max_dist",
        "max_laps",
        "name",
        "point_wait_ms",
        "points",
        "set_target",
        "timeout_ms",
        "wait_for_loot",
    ),
    node_class_name="AutoPathUntilEnemyNode",
)(handle_auto_path_until_enemy)
modular_step(
    step_type="auto_path_until_timeout",
    category="movement",
    allowed_params=(
        "lap_wait_ms",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "name",
        "point_wait_ms",
        "points",
        "timeout_ms",
        "wait_for_loot",
    ),
    node_class_name="AutoPathUntilTimeoutNode",
)(handle_auto_path_till_timeout)
modular_step(
    step_type="enter_challenge",
    category="movement",
    allowed_params=("delay", "delay_ms", "name", "target_map_id"),
    node_class_name="EnterChallengeNode",
)(handle_enter_challenge)
modular_step(
    step_type="exit_map",
    category="movement",
    allowed_params=(
        "name",
        "suppress_recovery_events",
        "suppress_recovery_ms",
        "target_map_id",
        "target_map_name",
    ),
    node_class_name="ExitMapNode",
)(handle_exit_map)
modular_step(
    step_type="follow_model",
    category="movement",
    allowed_params=("follow_range", "model_id", "range", "timeout_ms"),
    node_class_name="FollowModelNode",
)(handle_follow_model)
modular_step(
    step_type="leave_party",
    category="movement",
    allowed_params=("multibox", "name"),
    node_class_name="LeavePartyNode",
)(handle_leave_party)
modular_step(
    step_type="move",
    category="movement",
    allowed_params=("loot_wait_poll_ms", "loot_wait_range", "loot_wait_timeout_ms", "name", "wait_for_loot"),
    node_class_name="MoveNode",
)(handle_move)
modular_step(
    step_type="nudge",
    category="movement",
    allowed_params=("move_ms", "name", "pulse_ms", "pulses"),
    node_class_name="NudgeNode",
)(handle_nudge_move)
modular_step(
    step_type="nudge_move",
    category="movement",
    allowed_params=("move_ms", "name", "pulse_ms", "pulses"),
    node_class_name="NudgeMoveNode",
)(handle_nudge_move)
modular_step(
    step_type="path",
    category="movement",
    allowed_params=("loot_wait_poll_ms", "loot_wait_range", "loot_wait_timeout_ms", "name", "points", "wait_for_loot"),
    node_class_name="PathNode",
)(handle_path)
modular_step(
    step_type="path_to_target",
    category="movement",
    allowed_params=(
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "max_dist",
        "name",
        "required",
        "tolerance",
        "wait_for_loot",
    ),
    node_class_name="PathToTargetNode",
)(handle_path_to_target)
modular_step(
    step_type="patrol_until_enemy",
    category="movement",
    allowed_params=(
        "include_dead",
        "lap_wait_ms",
        "loot_wait_poll_ms",
        "loot_wait_range",
        "loot_wait_timeout_ms",
        "max_dist",
        "max_laps",
        "name",
        "point_wait_ms",
        "points",
        "set_target",
        "timeout_ms",
        "wait_for_loot",
    ),
    node_class_name="PatrolUntilEnemyNode",
)(handle_auto_path_until_enemy)
modular_step(
    step_type="random_travel",
    category="movement",
    allowed_params=("allowed_districts", "districts", "leave_party", "name", "target_map_id", "target_map_name", "travel_wait_ms"),
    node_class_name="RandomTravelNode",
)(handle_random_travel)
modular_step(
    step_type="travel",
    category="movement",
    allowed_params=("leave_party", "target_map_id", "target_map_name"),
    node_class_name="TravelNode",
)(handle_travel)
modular_step(
    step_type="travel_gh",
    category="movement",
    allowed_params=("multibox", "name", "per_account_delay_ms"),
    node_class_name="TravelGhNode",
)(handle_travel_gh)
modular_step(
    step_type="wait",
    category="movement",
    allowed_params=("name",),
    node_class_name="WaitNode",
)(handle_wait)
modular_step(
    step_type="wait_for_map_load",
    category="movement",
    allowed_params=("map_id", "target_map_id"),
    node_class_name="WaitForMapLoadNode",
)(handle_wait_map_load)
modular_step(
    step_type="wait_map_change",
    category="movement",
    allowed_params=("target_map_id",),
    node_class_name="WaitMapChangeNode",
)(handle_wait_map_change)
modular_step(
    step_type="wait_map_load",
    category="movement",
    allowed_params=("map_id", "target_map_id"),
    node_class_name="WaitMapLoadNode",
)(handle_wait_map_load)
modular_step(
    step_type="wait_out_of_combat",
    category="movement",
    allowed_params=(),
    node_class_name="WaitOutOfCombatNode",
)(handle_wait_out_of_combat)
