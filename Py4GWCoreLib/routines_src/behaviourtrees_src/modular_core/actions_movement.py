"""
actions_movement module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_movement import (
    add_enter_challenge_state,
    add_exit_map_state,
    add_follow_model_state,
    add_move_state,
    add_nudge_move_state,
    add_path_state,
    add_random_travel_state,
    add_wait_map_change_state,
    add_wait_map_load_state,
    add_wait_out_of_combat_state,
    dispatch_travel,
)
from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_multibox import (
    add_leave_party_state,
    add_travel_gh_state,
)
from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_pathing import add_path_to_target_state

from .actions_party_toggles import (
    apply_auto_combat_state,
    apply_auto_looting_state,
    current_auto_combat_enabled,
    current_auto_looting_enabled,
)
from .combat_engine import (
    party_loot_wait_required,
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
    add_path_state(ctx.bot, points, str(name))
    wait_after_step(ctx.bot, ctx.step)


def handle_wait(ctx: StepContext) -> None:
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_out_of_combat(ctx: StepContext) -> None:
    add_wait_out_of_combat_state(ctx.bot, str(ctx.step.get("name", "Wait Out Of Combat")))
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_load(ctx: StepContext) -> None:
    map_id = int(ctx.step.get("map_id", ctx.step.get("target_map_id", 0)) or 0)
    add_wait_map_load_state(ctx.bot, target_map_id=map_id, name=str(ctx.step.get("name", "Wait Map Load")))
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
    add_move_state(ctx.bot, x, y, str(name or f"Move {ctx.step_idx + 1}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_nudge_move(ctx: StepContext) -> None:
    coords = parse_step_point(ctx.step)
    if coords is None:
        log_recipe(ctx, f"nudge_move invalid coordinates at index {ctx.step_idx}: expected point [x, y].")
        wait_after_step(ctx.bot, ctx.step)
        return
    x, y = coords
    name = str(ctx.step.get("name", f"Nudge {ctx.step_idx + 1}") or f"Nudge {ctx.step_idx + 1}")
    pulses = max(1, parse_step_int(ctx.step.get("pulses", 1), 1))
    pulse_ms = max(0, parse_step_int(ctx.step.get("pulse_ms", ctx.step.get("move_ms", 250)), 250))
    add_nudge_move_state(ctx.bot, x, y, name=name, pulses=pulses, pulse_ms=pulse_ms)
    wait_after_step(ctx.bot, ctx.step)


def handle_path_to_target(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    max_dist = parse_step_float(ctx.step.get("max_dist", Range.Compass.value), Range.Compass.value)
    tolerance = parse_step_float(ctx.step.get("tolerance", 150.0), 150.0)
    required = parse_step_bool(ctx.step.get("required", True), True)
    step_name = ctx.step.get("name", "Path To Target")
    _add_pre_movement_loot_wait(ctx, str(step_name))

    if max_dist <= 0:
        max_dist = Range.Compass.value
    if tolerance <= 0:
        tolerance = 150.0

    def _resolve_target():
        return resolve_enemy_agent_id_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            default_max_dist=max_dist,
        )

    add_path_to_target_state(
        ctx.bot,
        target_resolver=_resolve_target,
        max_dist=max_dist,
        tolerance=tolerance,
        required=required,
        name=str(step_name),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_travel(ctx: StepContext) -> None:
    target_map_id = int(ctx.step.get("target_map_id", 0))
    target_map_name = str(ctx.step.get("target_map_name", "") or "")
    leave_party = parse_step_bool(ctx.step.get("leave_party", True), True)
    dispatch_travel(ctx.bot, target_map_id=target_map_id, target_map_name=target_map_name, leave_party=leave_party)
    wait_after_step(ctx.bot, ctx.step)


def handle_random_travel(ctx: StepContext) -> None:
    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)
    target_map_name = str(ctx.step.get("target_map_name", "") or "").strip()
    settle_wait_ms = parse_step_int(ctx.step.get("travel_wait_ms", 500), 500)
    leave_party = parse_step_bool(ctx.step.get("leave_party", True), True)
    raw_districts = ctx.step.get("districts", ctx.step.get("allowed_districts"))
    add_random_travel_state(
        ctx.bot,
        target_map_id=target_map_id,
        target_map_name=target_map_name,
        districts=raw_districts,
        leave_party=leave_party,
        settle_wait_ms=settle_wait_ms,
        name=str(ctx.step.get("name", f"Random Travel {ctx.step_idx + 1}")),
        log=lambda message: log_recipe(ctx, f"{message} step={ctx.step_idx + 1}"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_travel_gh(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    per_account_delay_ms = max(0, parse_step_int(ctx.step.get("per_account_delay_ms", 500), 500))
    add_travel_gh_state(
        ctx.bot,
        multibox=multibox,
        per_account_delay_ms=per_account_delay_ms,
        name=str(ctx.step.get("name", f"Travel GH {ctx.step_idx + 1}")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_leave_party(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    add_leave_party_state(
        ctx.bot,
        multibox=multibox,
        name=str(ctx.step.get("name", f"Leave Party {ctx.step_idx + 1}")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
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

    add_exit_map_state(
        ctx.bot,
        x=x,
        y=y,
        name=step_name,
        target_map_id=target_map_id,
        target_map_name=target_map_name,
    )

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
    model_id = int(str(ctx.step["model_id"]), 0)
    follow_range = float(ctx.step.get("follow_range", ctx.step.get("range", 600)))
    timeout_ms = int(ctx.step.get("timeout_ms", 0))
    add_follow_model_state(ctx.bot, model_id=model_id, follow_range=follow_range, timeout_ms=timeout_ms)
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_change(ctx: StepContext) -> None:
    add_wait_map_change_state(
        ctx.bot,
        target_map_id=parse_step_int(ctx.step.get("target_map_id", 0), 0),
        name=str(ctx.step.get("name", "Wait Map Change")),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_enter_challenge(ctx: StepContext) -> None:
    step_name = str(ctx.step.get("name", "Enter Challenge") or "Enter Challenge")
    delay_ms = parse_step_int(ctx.step.get("delay_ms", ctx.step.get("delay", 2000)), 2000)
    target_map_id = parse_step_int(ctx.step.get("target_map_id", 0), 0)
    add_enter_challenge_state(ctx.bot, name=step_name, delay_ms=delay_ms, target_map_id=target_map_id)
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
