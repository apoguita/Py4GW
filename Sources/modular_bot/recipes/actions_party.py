from __future__ import annotations

from typing import Callable

from .combat_engine import (
    ENGINE_CUSTOM_BEHAVIORS,
    ENGINE_HERO_AI,
    flag_all_accounts as engine_flag_all_accounts,
    resolve_active_engine,
    set_auto_combat as engine_set_auto_combat,
    set_auto_looting as engine_set_auto_looting,
    unflag_all_accounts as engine_unflag_all_accounts,
)
from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, wait_after_step


def handle_set_title(ctx: StepContext) -> None:
    ctx.bot.Player.SetTitle(ctx.step["id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_use_all_consumables(ctx: StepContext) -> None:
    ctx.bot.Items.UseAllConsumables()
    wait_after_step(ctx.bot, ctx.step)


def handle_drop_bundle(ctx: StepContext) -> None:
    from Py4GWCoreLib import Key, Keystroke

    ctx.bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F2").value), "F2 Drop Bundle")
    ctx.bot.Wait.ForTime(200)
    ctx.bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F1").value), "F1 Drop Bundle")
    ctx.bot.Wait.ForTime(200)
    wait_after_step(ctx.bot, ctx.step)


def handle_force_hero_state(ctx: StepContext) -> None:
    from Py4GWCoreLib import Party

    raw_state = str(ctx.step.get("state", "")).strip().lower()
    behavior_map = {
        "fight": 0,
        "guard": 1,
        "avoid": 2,
    }

    if "behavior" in ctx.step:
        try:
            behavior = int(ctx.step["behavior"])
        except (TypeError, ValueError):
            behavior = -1
    else:
        behavior = behavior_map.get(raw_state, -1)

    if behavior not in (0, 1, 2):
        debug_log_recipe(
            ctx,
            f"Invalid force_hero_state at index {ctx.step_idx}: state={raw_state!r}, behavior={ctx.step.get('behavior')!r}",
        )
        return

    state_name = ctx.step.get("name", f"Force Hero State ({raw_state or behavior})")

    def _set_hero_behavior_all(behavior_value: int = behavior) -> None:
        for hero in Party.GetHeroes():
            hero_agent_id = getattr(hero, "agent_id", 0)
            if hero_agent_id:
                Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)

    ctx.bot.States.AddCustomState(_set_hero_behavior_all, state_name)
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_heroes(ctx: StepContext) -> None:
    def _flag_heroes() -> None:
        ctx.bot.Party.FlagAllHeroes(ctx.step["x"], ctx.step["y"])

    ctx.bot.States.AddCustomState(_flag_heroes, ctx.step.get("name", "Flag Heroes"))
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_all_accounts(ctx: StepContext) -> None:
    def _flag_all_accounts() -> None:
        x = float(ctx.step["x"])
        y = float(ctx.step["y"])
        try:
            changed = int(engine_flag_all_accounts(x, y))
        except Exception as exc:
            debug_log_recipe(ctx, f"flag_all_accounts failed at index {ctx.step_idx}: {exc}")
            return

        if changed:
            debug_log_recipe(ctx, f"flag_all_accounts applied to {changed} account(s).")
        else:
            debug_log_recipe(ctx, "flag_all_accounts had no eligible accounts.")

    ctx.bot.States.AddCustomState(
        _flag_all_accounts,
        ctx.step.get("name", "Flag All Accounts"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_heroes(ctx: StepContext) -> None:
    ctx.bot.Party.UnflagAllHeroes()
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_all_accounts(ctx: StepContext) -> None:
    def _unflag_all_accounts() -> None:
        changed = int(engine_unflag_all_accounts())
        debug_log_recipe(ctx, f"unflag_all_accounts cleared flags for {changed} account(s).")

    ctx.bot.States.AddCustomState(
        _unflag_all_accounts,
        ctx.step.get("name", "Unflag All Accounts"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_resign(ctx: StepContext) -> None:
    ctx.bot.Multibox.ResignParty()
    wait_after_step(ctx.bot, ctx.step)


def handle_summon_all_accounts(ctx: StepContext) -> None:
    ctx.bot.Multibox.SummonAllAccounts()
    wait_after_step(ctx.bot, ctx.step)


def handle_invite_all_accounts(ctx: StepContext) -> None:
    ctx.bot.Multibox.InviteAllAccounts()
    wait_after_step(ctx.bot, ctx.step)


def handle_set_anchor(ctx: StepContext) -> None:
    target = str(ctx.step.get("phase", ctx.step.get("target", ctx.step.get("name", ""))) or "").strip()
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "set_anchor"):
        debug_log_recipe(ctx, f"set_anchor requires ModularBot owner; step index {ctx.step_idx}")
        return
    if not target:
        current_state = ctx.bot.config.FSM.current_state
        target = str(getattr(current_state, "name", "") or "").strip()
    if not owner.set_anchor(target):
        debug_log_recipe(ctx, f"set_anchor could not resolve target at index {ctx.step_idx}: {target!r}")
        return
    wait_after_step(ctx.bot, ctx.step)


def handle_set_auto_combat(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)

    def _set_auto_combat_runtime(e: bool = enabled) -> None:
        engine = resolve_active_engine()
        engine_set_auto_combat(e)
        # Keep template-driven toggles from clobbering external combat engines.
        if engine == ENGINE_HERO_AI:
            if ctx.bot.Properties.exists("hero_ai"):
                ctx.bot.Properties.ApplyNow("hero_ai", "active", True)
            if ctx.bot.Properties.exists("auto_combat"):
                ctx.bot.Properties.ApplyNow("auto_combat", "active", False)
            return
        if engine == ENGINE_CUSTOM_BEHAVIORS:
            if ctx.bot.Properties.exists("hero_ai"):
                ctx.bot.Properties.ApplyNow("hero_ai", "active", False)
            if ctx.bot.Properties.exists("auto_combat"):
                ctx.bot.Properties.ApplyNow("auto_combat", "active", False)
            return

        if e:
            ctx.bot.Templates.Aggressive()
        else:
            ctx.bot.Templates.Pacifist()

    ctx.bot.States.AddCustomState(
        _set_auto_combat_runtime,
        f"Set Combat {'On' if enabled else 'Off'}",
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_set_auto_looting(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)

    def _set_auto_looting_runtime(e: bool = enabled) -> None:
        engine = resolve_active_engine()
        engine_set_auto_looting(e)
        # External engines: keep Botting auto-loot in sync with requested
        # looting state.
        if engine == ENGINE_CUSTOM_BEHAVIORS:
            if ctx.bot.Properties.exists("auto_loot"):
                ctx.bot.Properties.ApplyNow("auto_loot", "active", bool(e))
            return
        # HeroAI mode: keep Botting auto-loot in sync with requested looting state.
        if engine == ENGINE_HERO_AI:
            if ctx.bot.Properties.exists("auto_loot"):
                ctx.bot.Properties.ApplyNow("auto_loot", "active", bool(e))
            return

        if e:
            ctx.bot.Properties.Enable("auto_loot")
        else:
            ctx.bot.Properties.Disable("auto_loot")

    ctx.bot.States.AddCustomState(
        _set_auto_looting_runtime,
        f"Set Looting {'On' if enabled else 'Off'}",
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_set_hard_mode(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)
    ctx.bot.Party.SetHardMode(enabled)
    wait_after_step(ctx.bot, ctx.step)


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "set_title": handle_set_title,
    "use_all_consumables": handle_use_all_consumables,
    "drop_bundle": handle_drop_bundle,
    "force_hero_state": handle_force_hero_state,
    "flag_heroes": handle_flag_heroes,
    "flag_all_accounts": handle_flag_all_accounts,
    "unflag_heroes": handle_unflag_heroes,
    "unflag_all_accounts": handle_unflag_all_accounts,
    "resign": handle_resign,
    "summon_all_accounts": handle_summon_all_accounts,
    "invite_all_accounts": handle_invite_all_accounts,
    "set_anchor": handle_set_anchor,
    "set_auto_combat": handle_set_auto_combat,
    "set_auto_looting": handle_set_auto_looting,
    "set_hard_mode": handle_set_hard_mode,
}
