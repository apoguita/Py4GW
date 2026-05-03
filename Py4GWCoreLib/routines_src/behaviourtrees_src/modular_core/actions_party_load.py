"""
actions_party_load module

This module provides party loading step handlers.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_party_load import add_load_party_state

from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, parse_step_int, wait_after_step


def handle_load_party(ctx: StepContext) -> None:
    clear_existing = parse_step_bool(ctx.step.get("clear_existing", True), True)
    raw_hero_team = str(ctx.step.get("hero_team", ctx.step.get("team", "")) or "").strip()
    team_mode = str(ctx.step.get("team_mode", ctx.step.get("team_selection", "")) or "").strip().lower()
    use_priority = parse_step_bool(ctx.step.get("use_priority", False), False)
    fill_with_henchmen = parse_step_bool(ctx.step.get("fill_with_henchmen", False), False)
    apply_hero_templates = parse_step_bool(ctx.step.get("apply_templates", True), True)
    if team_mode == "priority":
        raw_hero_team = "priority"
        use_priority = True
    elif team_mode == "exact":
        use_priority = False
    elif team_mode == "henchman":
        use_priority = False
        fill_with_henchmen = True
    if use_priority:
        raw_hero_team = "priority"

    minionless = parse_step_bool(ctx.step.get("minionless", False), False)
    requested_team_key = "" if raw_hero_team.lower() == "priority" else raw_hero_team
    requested_max_heroes = parse_step_int(ctx.step.get("max_heroes", 0), 0)
    wait_timeout_ms = max(0, parse_step_int(ctx.step.get("wait_timeout_ms", 12_000), 12_000))
    wait_poll_ms = max(50, parse_step_int(ctx.step.get("wait_poll_ms", 250), 250))
    add_delay_ms = max(0, parse_step_int(ctx.step.get("add_delay_ms", 150), 150))

    add_load_party_state(
        ctx.bot,
        step=ctx.step,
        clear_existing=clear_existing,
        raw_hero_team=raw_hero_team,
        team_mode=team_mode,
        use_priority=use_priority,
        fill_with_henchmen=fill_with_henchmen,
        apply_hero_templates=apply_hero_templates,
        minionless=minionless,
        requested_team_key=requested_team_key,
        requested_max_heroes=requested_max_heroes,
        wait_timeout_ms=wait_timeout_ms,
        wait_poll_ms=wait_poll_ms,
        add_delay_ms=add_delay_ms,
        name=str(ctx.step.get("name", "Load Party")),
        log=lambda message: debug_log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)
