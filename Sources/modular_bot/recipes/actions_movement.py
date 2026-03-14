from __future__ import annotations

import random
from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_enemy_agent_id_from_step
from .step_utils import parse_step_bool, parse_step_float, parse_step_int, wait_after_step, log_recipe


def handle_path(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"Path {ctx.step_idx + 1}")
    ctx.bot.Move.FollowAutoPath(points, step_name=name)
    wait_after_step(ctx.bot, ctx.step)


def handle_auto_path(ctx: StepContext) -> None:
    points = [tuple(p) for p in ctx.step["points"]]
    name = ctx.step.get("name", f"AutoPath {ctx.step_idx + 1}")
    pause_on_combat = parse_step_bool(ctx.step.get("pause_on_combat", False), False)
    pause_on_danger_was_active = bool(ctx.bot.Properties.IsActive("pause_on_danger"))

    if pause_on_combat:
        # Enable before movement executes (FSM runtime), not during step registration.
        ctx.bot.States.AddCustomState(
            lambda: ctx.bot.Properties.ApplyNow("pause_on_danger", "active", True),
            f"{name}: Enable Pause On Combat",
        )

    ctx.bot.Move.FollowAutoPath(points, step_name=name)

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
    if delay_ms < 0:
        delay_ms = 0
    for point_i, (x, y) in enumerate(points):
        step_name = f"{name} [{point_i + 1}/{len(points)}]"
        ctx.bot.Move.XY(x, y, step_name=step_name)
        if point_i < len(points) - 1 and delay_ms > 0:
            ctx.bot.Wait.ForTime(delay_ms)
    wait_after_step(ctx.bot, ctx.step)


def handle_wait(ctx: StepContext) -> None:
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_out_of_combat(ctx: StepContext) -> None:
    ctx.bot.Wait.UntilOutOfCombat()
    wait_after_step(ctx.bot, ctx.step)


def handle_wait_map_load(ctx: StepContext) -> None:
    ctx.bot.Wait.ForMapLoad(target_map_id=ctx.step["map_id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_move(ctx: StepContext) -> None:
    x, y = ctx.step["x"], ctx.step["y"]
    name = ctx.step.get("name", "")
    ctx.bot.Move.XY(x, y, step_name=name)
    wait_after_step(ctx.bot, ctx.step)


def handle_path_to_target(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, Player, Range, Utils

    max_dist = parse_step_float(ctx.step.get("max_dist", Range.Compass.value), Range.Compass.value)
    tolerance = parse_step_float(ctx.step.get("tolerance", 150.0), 150.0)
    required = parse_step_bool(ctx.step.get("required", True), True)
    step_name = ctx.step.get("name", "Path To Target")

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

    district = int(random.choice(allowed_districts))

    def _travel() -> None:
        Map.TravelToDistrict(target_map_id, district=district)

    ctx.bot.States.AddCustomState(_travel, ctx.step.get("name", f"Random Travel {ctx.step_idx + 1}"))
    if settle_wait_ms > 0:
        ctx.bot.Wait.ForTime(settle_wait_ms)
    ctx.bot.Wait.ForMapLoad(target_map_id=target_map_id)
    wait_after_step(ctx.bot, ctx.step)


def handle_travel_gh(ctx: StepContext) -> None:
    from Py4GWCoreLib import ConsoleLog, Map, Routines

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    wait_time = int(ctx.step.get("ms", ctx.step.get("wait_time", 4000)))

    def _safe_local_travel_gh() -> None:
        if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                "travel_gh requested while explorable; resigning to outpost first.",
            )
            ctx.bot.Multibox.ResignParty()
            ctx.bot.Wait.UntilOnOutpost()
            ctx.bot.Wait.ForTime(1000)

        if Map.IsGuildHall():
            ConsoleLog(f"Recipe:{ctx.recipe_name}", "Already in Guild Hall; skipping TravelGH.")
            return

        ctx.bot.Map.TravelGH(wait_time=wait_time)

    if multibox:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )
        from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import (
            PartyCommandConstants,
        )

        ctx.bot.Wait.UntilCondition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)

        def _schedule_cb_travel_gh() -> None:
            ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh))
            if not ok:
                ConsoleLog(
                    f"Recipe:{ctx.recipe_name}",
                    "travel_gh multibox schedule failed; falling back to local TravelGH().",
                )
                _safe_local_travel_gh()

        ctx.bot.States.AddCustomState(_schedule_cb_travel_gh, "Schedule CB Travel GH")
        ctx.bot.Wait.UntilCondition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
    else:
        _safe_local_travel_gh()
    wait_after_step(ctx.bot, ctx.step)


def handle_leave_party(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)

    if multibox:
        from Py4GWCoreLib import ConsoleLog
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )
        from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import (
            PartyCommandConstants,
        )

        ctx.bot.Wait.UntilCondition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)

        def _schedule_cb_leave_party() -> None:
            ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.leave_current_party))
            if not ok:
                ConsoleLog(
                    f"Recipe:{ctx.recipe_name}",
                    "leave_party multibox schedule failed; falling back to local LeaveParty().",
                )
                ctx.bot.Party.LeaveParty()

        ctx.bot.States.AddCustomState(_schedule_cb_leave_party, "Schedule CB Leave Party")
        ctx.bot.Wait.UntilCondition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
    else:
        ctx.bot.Party.LeaveParty()
    wait_after_step(ctx.bot, ctx.step)


def handle_exit_map(ctx: StepContext) -> None:
    x, y = ctx.step["x"], ctx.step["y"]
    target_map_id = ctx.step.get("target_map_id", 0)
    ctx.bot.Move.XYAndExitMap(x, y, target_map_id=target_map_id, step_name=ctx.step.get("name", "Exit Map"))
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


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "path": handle_path,
    "auto_path": handle_auto_path,
    "auto_path_delayed": handle_auto_path_delayed,
    "wait": handle_wait,
    "wait_out_of_combat": handle_wait_out_of_combat,
    "wait_map_load": handle_wait_map_load,
    "move": handle_move,
    "path_to_target": handle_path_to_target,
    "travel": handle_travel,
    "random_travel": handle_random_travel,
    "travel_gh": handle_travel_gh,
    "leave_party": handle_leave_party,
    "exit_map": handle_exit_map,
    "follow_model": handle_follow_model,
    "wait_map_change": handle_wait_map_change,
}
