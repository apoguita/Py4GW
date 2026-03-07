from __future__ import annotations

from typing import Callable

from .step_context import StepContext
from .step_utils import parse_step_bool, wait_after_step


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
    from Py4GWCoreLib import ConsoleLog, Party

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
        ConsoleLog(
            f"Recipe:{ctx.recipe_name}",
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
    from Py4GWCoreLib import ConsoleLog
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
        CustomBehaviorParty,
    )

    def _flag_all_accounts() -> None:
        x = float(ctx.step["x"])
        y = float(ctx.step["y"])
        party = CustomBehaviorParty()
        assigned = party.party_flagging_manager.auto_assign_emails_if_none_assigned()

        try:
            party.party_flagging_manager.update_formation_positions(x, y, 0.0, formation_type="preset_2")
        except Exception as exc:
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                f"flag_all_accounts failed at index {ctx.step_idx}: {exc}",
            )
            return

        if assigned:
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                "flag_all_accounts auto-assigned current party emails to shared flags.",
            )

    ctx.bot.States.AddCustomState(
        _flag_all_accounts,
        ctx.step.get("name", "Flag All Accounts"),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_heroes(ctx: StepContext) -> None:
    ctx.bot.Party.UnflagAllHeroes()
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_all_accounts(ctx: StepContext) -> None:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
        CustomBehaviorParty,
    )

    ctx.bot.States.AddCustomState(
        lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flag_positions(),
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
    from Py4GWCoreLib import ConsoleLog

    target = str(ctx.step.get("phase", ctx.step.get("target", ctx.step.get("name", ""))) or "").strip()
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "set_anchor"):
        ConsoleLog(
            f"Recipe:{ctx.recipe_name}",
            f"set_anchor requires ModularBot owner; step index {ctx.step_idx}",
        )
        return
    if not target:
        current_state = ctx.bot.config.FSM.current_state
        target = str(getattr(current_state, "name", "") or "").strip()
    if not owner.set_anchor(target):
        ConsoleLog(
            f"Recipe:{ctx.recipe_name}",
            f"set_anchor could not resolve target at index {ctx.step_idx}: {target!r}",
        )
        return
    wait_after_step(ctx.bot, ctx.step)


def handle_set_auto_combat(ctx: StepContext) -> None:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
        CustomBehaviorParty,
    )

    enabled = parse_step_bool(ctx.step.get("enabled", True), True)

    ctx.bot.States.AddCustomState(
        lambda e=enabled: CustomBehaviorParty().set_party_is_combat_enabled(e),
        f"Set CB Combat {'On' if enabled else 'Off'}",
    )
    if enabled:
        ctx.bot.Templates.Aggressive()
    else:
        ctx.bot.Templates.Pacifist()
    wait_after_step(ctx.bot, ctx.step)


def handle_set_auto_looting(ctx: StepContext) -> None:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
        CustomBehaviorParty,
    )

    enabled = parse_step_bool(ctx.step.get("enabled", True), True)

    ctx.bot.States.AddCustomState(
        lambda e=enabled: CustomBehaviorParty().set_party_is_looting_enabled(e),
        f"Set CB Looting {'On' if enabled else 'Off'}",
    )

    if enabled:
        ctx.bot.Properties.Enable("auto_loot")
    else:
        ctx.bot.Properties.Disable("auto_loot")
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
