from __future__ import annotations

from typing import Callable

from .combat_engine import (
    ENGINE_CUSTOM_BEHAVIORS,
    ENGINE_HERO_AI,
    flag_all_accounts as engine_flag_all_accounts,
    resolve_engine_for_bot,
    set_auto_combat as engine_set_auto_combat,
    set_auto_looting as engine_set_auto_looting,
    unflag_all_accounts as engine_unflag_all_accounts,
)
from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, parse_step_int, wait_after_step


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
    from Py4GWCoreLib import Map, Party

    def _flag_heroes() -> None:
        if not Map.IsExplorable():
            debug_log_recipe(ctx, "flag_heroes skipped: map is not explorable.")
            return

        hero_count = int(Party.GetHeroCount() or 0)
        if hero_count <= 0:
            debug_log_recipe(ctx, "flag_heroes skipped: no heroes in party.")
            return

        try:
            x = float(ctx.step["x"])
            y = float(ctx.step["y"])
        except (TypeError, ValueError, KeyError):
            debug_log_recipe(ctx, f"flag_heroes invalid coordinates at index {ctx.step_idx}: {ctx.step!r}")
            return

        Party.Heroes.FlagAllHeroes(x, y)

    ctx.bot.States.AddCustomState(_flag_heroes, ctx.step.get("name", "Flag Heroes"))
    wait_after_step(ctx.bot, ctx.step)


def handle_flag_all_accounts(ctx: StepContext) -> None:
    def _flag_all_accounts() -> None:
        x = float(ctx.step["x"])
        y = float(ctx.step["y"])
        engine = resolve_engine_for_bot(ctx.bot)
        try:
            changed = int(engine_flag_all_accounts(x, y, preferred_engine=engine, bot=ctx.bot))
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
    from Py4GWCoreLib import Party

    def _unflag_heroes() -> None:
        Party.Heroes.UnflagAllHeroes()

    ctx.bot.States.AddCustomState(_unflag_heroes, ctx.step.get("name", "Unflag Heroes"))
    wait_after_step(ctx.bot, ctx.step)


def handle_unflag_all_accounts(ctx: StepContext) -> None:
    def _unflag_all_accounts() -> None:
        engine = resolve_engine_for_bot(ctx.bot)
        changed = int(engine_unflag_all_accounts(preferred_engine=engine, bot=ctx.bot))
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
        # Keep movement behavior aligned with requested combat state.
        # If combat is disabled, avoid pause-on-danger halts when enemies aggro.
        if ctx.bot.Properties.exists("pause_on_danger"):
            ctx.bot.Properties.ApplyNow("pause_on_danger", "active", bool(e))

        engine = resolve_engine_for_bot(ctx.bot)
        engine_set_auto_combat(e, preferred_engine=engine, bot=ctx.bot)
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
        engine = resolve_engine_for_bot(ctx.bot)
        engine_set_auto_looting(e, preferred_engine=engine, bot=ctx.bot)
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


def handle_heroes_use_skill(ctx: StepContext) -> None:
    from Py4GWCoreLib import Party

    try:
        slot = parse_step_int(ctx.step.get("slot", 0), 0)
    except Exception:
        slot = 0
    if slot < 1 or slot > 8:
        debug_log_recipe(ctx, f"heroes_use_skill invalid slot at index {ctx.step_idx}: {ctx.step.get('slot')!r}")
        return

    target_id = parse_step_int(ctx.step.get("target_id", 0), 0)

    def _heroes_use_skill() -> None:
        heroes = Party.GetHeroes() or []
        used = 0
        for hero in heroes:
            hero_agent_id = int(getattr(hero, "agent_id", 0) or 0)
            if hero_agent_id <= 0:
                continue
            Party.Heroes.UseSkill(hero_agent_id, int(slot), int(target_id))
            used += 1
        if used == 0:
            debug_log_recipe(ctx, "heroes_use_skill skipped: no heroes available.")

    ctx.bot.States.AddCustomState(_heroes_use_skill, ctx.step.get("name", f"Heroes Use Skill {slot}"))
    wait_after_step(ctx.bot, ctx.step)


def handle_set_party_member_hooks(ctx: StepContext) -> None:
    enabled = parse_step_bool(ctx.step.get("enabled", True), True)
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "set_party_member_hooks_enabled"):
        debug_log_recipe(ctx, f"set_party_member_hooks requires ModularBot owner; step index {ctx.step_idx}")
        return

    def _set_party_member_hooks() -> None:
        owner.set_party_member_hooks_enabled(enabled)

    label = str(ctx.step.get("name", f"{'Enable' if enabled else 'Disable'} Party Member Hooks") or "").strip()
    ctx.bot.States.AddCustomState(_set_party_member_hooks, label or "Set Party Member Hooks")
    wait_after_step(ctx.bot, ctx.step)


def handle_disable_party_member_hooks(ctx: StepContext) -> None:
    step = dict(ctx.step)
    step["enabled"] = False
    proxy_ctx = StepContext(
        bot=ctx.bot,
        step=step,
        step_idx=ctx.step_idx,
        recipe_name=ctx.recipe_name,
        step_type=ctx.step_type,
        step_display=ctx.step_display,
    )
    handle_set_party_member_hooks(proxy_ctx)


def handle_enable_party_member_hooks(ctx: StepContext) -> None:
    step = dict(ctx.step)
    step["enabled"] = True
    proxy_ctx = StepContext(
        bot=ctx.bot,
        step=step,
        step_idx=ctx.step_idx,
        recipe_name=ctx.recipe_name,
        step_type=ctx.step_type,
        step_display=ctx.step_display,
    )
    handle_set_party_member_hooks(proxy_ctx)


def handle_suppress_recovery(ctx: StepContext) -> None:
    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "suppress_recovery_for"):
        debug_log_recipe(ctx, f"suppress_recovery requires ModularBot owner; step index {ctx.step_idx}")
        return

    ms = max(0, parse_step_int(ctx.step.get("ms", 45_000), 45_000))
    max_events = max(0, parse_step_int(ctx.step.get("max_events", 20), 20))
    until_outpost = parse_step_bool(ctx.step.get("until_outpost", False), False)

    def _suppress() -> None:
        owner.suppress_recovery_for(ms=ms, max_events=max_events, until_outpost=until_outpost)
        debug_log_recipe(
            ctx,
            f"suppress_recovery active for {ms} ms, max_events={max_events}, until_outpost={until_outpost}.",
        )

    ctx.bot.States.AddCustomState(_suppress, ctx.step.get("name", "Suppress Recovery"))
    wait_after_step(ctx.bot, ctx.step)


def handle_load_party(ctx: StepContext) -> None:
    from time import monotonic

    from Py4GWCoreLib import Map, Party, Routines
    from Sources.modular_bot.hero_setup import (
        get_hero_priority,
        get_team_for_size,
        load_hero_templates,
        resolve_hero_ids,
    )

    minionless = parse_step_bool(ctx.step.get("minionless", False), False)
    clear_existing = parse_step_bool(ctx.step.get("clear_existing", True), True)
    use_priority = parse_step_bool(ctx.step.get("use_priority", True), True)
    team_mode = str(ctx.step.get("team_mode", ctx.step.get("team_selection", "")) or "").strip().lower()
    fill_with_henchmen = parse_step_bool(ctx.step.get("fill_with_henchmen", False), False)
    apply_hero_templates = parse_step_bool(ctx.step.get("apply_templates", True), True)
    if team_mode == "priority":
        use_priority = True
    elif team_mode == "exact":
        use_priority = False
    elif team_mode == "henchman":
        use_priority = False
        fill_with_henchmen = True
    requested_team_key = str(ctx.step.get("team", ctx.step.get("hero_team", "")) or "").strip()
    requested_max_heroes = parse_step_int(ctx.step.get("max_heroes", 0), 0)

    wait_timeout_ms = max(0, parse_step_int(ctx.step.get("wait_timeout_ms", 12_000), 12_000))
    wait_poll_ms = max(50, parse_step_int(ctx.step.get("wait_poll_ms", 250), 250))
    add_delay_ms = max(0, parse_step_int(ctx.step.get("add_delay_ms", 150), 150))
    expected_holder = {"count": 0, "team": requested_team_key, "wait_for_npc_count": bool(fill_with_henchmen or team_mode == "henchman")}

    def _load_party():
        def _hench_count() -> int:
            try:
                return int(Party.GetHenchmanCount() or 0)
            except Exception:
                pass
            try:
                return int(len(Party.GetHenchmen() or []))
            except Exception:
                return 0

        def _npc_count() -> int:
            return int(Party.GetHeroCount() or 0) + int(_hench_count())

        def _hero_id_from_member(hero_member) -> int:
            try:
                hero_id_obj = getattr(hero_member, "hero_id", None)
                if hero_id_obj is None:
                    return 0
                if hasattr(hero_id_obj, "GetID"):
                    return int(hero_id_obj.GetID() or 0)
                return int(hero_id_obj or 0)
            except Exception:
                return 0

        def _hero_party_index_one_based(hero_id: int) -> int:
            heroes = Party.GetHeroes() or []
            for idx, hero in enumerate(heroes, start=1):
                if _hero_id_from_member(hero) == int(hero_id):
                    return int(idx)
            return 0

        runtime_team_key = requested_team_key
        runtime_max_heroes = int(requested_max_heroes)
        required_hero_ids = resolve_hero_ids(ctx.step.get("required_hero"))
        hero_templates = load_hero_templates() if apply_hero_templates else {}

        map_party_size = int(Map.GetMaxPartySize() or 0)
        if map_party_size <= 0:
            map_party_size = int(Party.GetPartySize() or 0)

        if not runtime_team_key:
            if runtime_max_heroes in (4, 6, 8):
                if runtime_max_heroes == 4:
                    runtime_team_key = "party_4"
                elif runtime_max_heroes == 6:
                    runtime_team_key = "party_6_no_spirits_minions" if minionless else "party_6"
                else:
                    runtime_team_key = "party_8"
            else:
                if map_party_size >= 8:
                    runtime_team_key = "party_8"
                elif map_party_size >= 6:
                    runtime_team_key = "party_6_no_spirits_minions" if minionless else "party_6"
                elif map_party_size >= 4:
                    runtime_team_key = "party_4"
                else:
                    runtime_team_key = "party_6_no_spirits_minions" if minionless else "party_6"

        if minionless and runtime_team_key == "party_6":
            runtime_team_key = "party_6_no_spirits_minions"

        if runtime_max_heroes <= 0:
            if runtime_team_key.startswith("party_4"):
                runtime_max_heroes = 4
            elif runtime_team_key.startswith("party_8"):
                runtime_max_heroes = 8
            else:
                runtime_max_heroes = 6

        if use_priority:
            # In priority mode we keep a full candidate pool so unavailable heroes
            # can be skipped and we still fill remaining slots.
            hero_ids = []
            for hid in required_hero_ids:
                ihid = int(hid or 0)
                if ihid > 0 and ihid not in hero_ids:
                    hero_ids.append(ihid)
            for hid in (get_hero_priority() or []):
                ihid = int(hid or 0)
                if ihid > 0 and ihid not in hero_ids:
                    hero_ids.append(ihid)
        else:
            hero_ids = list(get_team_for_size(runtime_max_heroes, runtime_team_key) or [])
        if (team_mode != "henchman") and (not fill_with_henchmen) and not hero_ids and not required_hero_ids:
            debug_log_recipe(
                ctx,
                (
                    "load_party skipped: no heroes resolved "
                    f"(team={runtime_team_key!r}, max_heroes={runtime_max_heroes}, minionless={minionless})"
                ),
            )
            expected_holder["count"] = 0
            expected_holder["team"] = runtime_team_key
            return

        hero_slot_cap = max(0, map_party_size - 1) if map_party_size > 0 else len(hero_ids)
        requested_slot_cap = max(0, int(runtime_max_heroes) - 1) if runtime_max_heroes > 0 else len(hero_ids)
        if requested_slot_cap > 0:
            hero_slot_cap = min(hero_slot_cap, requested_slot_cap) if hero_slot_cap > 0 else requested_slot_cap

        if (not use_priority) and hero_slot_cap > 0 and len(hero_ids) > hero_slot_cap:
            debug_log_recipe(
                ctx,
                f"load_party trimming heroes for map party size {map_party_size}: {len(hero_ids)} -> {hero_slot_cap}",
            )
            hero_ids = hero_ids[:hero_slot_cap]

        missing_required_ids = [hero_id for hero_id in required_hero_ids if hero_id not in hero_ids]
        if (not use_priority) and missing_required_ids:
            replace_count = len(missing_required_ids)
            if replace_count >= len(hero_ids):
                hero_ids = list(missing_required_ids)
            else:
                hero_ids = hero_ids[:-replace_count] + missing_required_ids

            if hero_slot_cap > 0 and len(hero_ids) > hero_slot_cap:
                hero_ids = hero_ids[-hero_slot_cap:]

            debug_log_recipe(
                ctx,
                (
                    "load_party applied required heroes "
                    f"(required={required_hero_ids}, missing={missing_required_ids}, team={runtime_team_key!r})"
                ),
            )

        expected_holder["count"] = int(min(len(hero_ids), hero_slot_cap if hero_slot_cap > 0 else len(hero_ids)))
        expected_holder["team"] = runtime_team_key

        if not Party.IsPartyLeader():
            debug_log_recipe(ctx, "load_party skipped: not party leader.")
            return
        if not Map.IsOutpost():
            debug_log_recipe(ctx, "load_party skipped: can only add heroes in outpost.")
            return
        if clear_existing:
            Party.Heroes.KickAllHeroes()
            if add_delay_ms > 0:
                yield from Routines.Yield.wait(add_delay_ms)

        existing_hero_ids: set[int] = set()
        for hero in Party.GetHeroes() or []:
            hid = _hero_id_from_member(hero)
            if hid > 0:
                existing_hero_ids.add(hid)

        target_count = int(hero_slot_cap if hero_slot_cap > 0 else len(hero_ids))
        player_count = max(1, int(Party.GetPlayerCount() or 1))
        if map_party_size > 0:
            npc_target_count = max(0, int(map_party_size) - int(player_count))
        else:
            npc_target_count = int(target_count)
        if runtime_max_heroes > 0:
            npc_target_count = min(npc_target_count, max(0, int(runtime_max_heroes) - int(player_count)))
        if npc_target_count <= 0:
            npc_target_count = int(target_count)
        if target_count <= 0:
            expected_holder["count"] = int(_npc_count() if expected_holder.get("wait_for_npc_count") else (Party.GetHeroCount() or 0))
            return

        if team_mode != "henchman":
            for hero_id in hero_ids:
                if int(Party.GetHeroCount() or 0) >= target_count:
                    break
                hid = int(hero_id or 0)
                if hid <= 0 or hid in existing_hero_ids:
                    continue

                before = int(Party.GetHeroCount() or 0)
                Party.Heroes.AddHero(hid)
                if add_delay_ms > 0:
                    yield from Routines.Yield.wait(add_delay_ms)
                after = int(Party.GetHeroCount() or 0)

                if after > before:
                    existing_hero_ids.add(hid)
                    if apply_hero_templates:
                        template_code = str((hero_templates or {}).get(str(hid), "") or "").strip()
                        if template_code:
                            hero_index = _hero_party_index_one_based(hid)
                            if hero_index > 0:
                                try:
                                    yield from Routines.Yield.Skills.LoadHeroSkillbar(
                                        int(hero_index), template_code, log=False
                                    )
                                    debug_log_recipe(
                                        ctx,
                                        f"load_party applied template for hero_id={hid} at hero_index={hero_index}.",
                                    )
                                except Exception as exc:
                                    debug_log_recipe(
                                        ctx,
                                        f"load_party failed applying template for hero_id={hid}: {exc}",
                                    )
                            else:
                                debug_log_recipe(
                                    ctx,
                                    f"load_party could not resolve hero index for template apply (hero_id={hid}).",
                                )
                else:
                    debug_log_recipe(
                        ctx,
                        f"load_party skipped unavailable/locked hero_id={hid}.",
                    )

        if fill_with_henchmen or team_mode == "henchman":
            raw_hench = ctx.step.get("henchman_ids", ctx.step.get("henchmen", []))
            hench_candidates: list[int] = []
            if isinstance(raw_hench, list):
                for value in raw_hench:
                    try:
                        hid = int(value)
                    except Exception:
                        continue
                    if hid > 0 and hid not in hench_candidates:
                        hench_candidates.append(hid)
            elif raw_hench is not None:
                try:
                    hid = int(raw_hench)
                except Exception:
                    hid = 0
                if hid > 0:
                    hench_candidates.append(hid)
            if not hench_candidates:
                hench_candidates = list(range(1, 33))

            for hench_id in hench_candidates:
                if int(_npc_count()) >= int(npc_target_count):
                    break
                before_npc = int(_npc_count())
                Party.Henchmen.AddHenchman(int(hench_id))
                if add_delay_ms > 0:
                    yield from Routines.Yield.wait(add_delay_ms)
                after_npc = int(_npc_count())
                if after_npc <= before_npc:
                    debug_log_recipe(ctx, f"load_party skipped unavailable henchman_id={int(hench_id)}.")

        final_count = int(Party.GetHeroCount() or 0)
        final_npc_count = int(_npc_count())
        if fill_with_henchmen or team_mode == "henchman":
            expected_holder["count"] = int(min(npc_target_count, final_npc_count))
        else:
            expected_holder["count"] = int(min(target_count, final_count))

        if required_hero_ids:
            missing_required = [hid for hid in required_hero_ids if hid not in existing_hero_ids]
            if missing_required:
                debug_log_recipe(
                    ctx,
                    f"load_party missing required heroes after add: {missing_required}.",
                )

    ctx.bot.States.AddCustomState(_load_party, ctx.step.get("name", "Load Party"))

    if wait_timeout_ms > 0:
        def _wait_for_party_load() -> None:
            expected = int(expected_holder.get("count", 0) or 0)
            if expected <= 0:
                return
            wait_for_npc_count = bool(expected_holder.get("wait_for_npc_count", False))
            deadline = monotonic() + (wait_timeout_ms / 1000.0)
            while monotonic() < deadline:
                current_count = int((Party.GetHeroCount() or 0) + (Party.GetHenchmanCount() or 0)) if wait_for_npc_count else int(Party.GetHeroCount() or 0)
                if Party.IsPartyLoaded() and current_count >= expected:
                    return
                yield from Routines.Yield.wait(wait_poll_ms)

            actual = int((Party.GetHeroCount() or 0) + (Party.GetHenchmanCount() or 0)) if wait_for_npc_count else int(Party.GetHeroCount() or 0)
            debug_log_recipe(
                ctx,
                (
                    "load_party timed out waiting for heroes "
                    f"(expected={expected}, actual={actual}, team={expected_holder.get('team')!r}, timeout_ms={wait_timeout_ms}). "
                    "Continuing."
                ),
            )

        ctx.bot.States.AddCustomState(_wait_for_party_load, f"{ctx.step.get('name', 'Load Party')}: Wait")

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
    "heroes_use_skill": handle_heroes_use_skill,
    "set_party_member_hooks": handle_set_party_member_hooks,
    "disable_party_member_hooks": handle_disable_party_member_hooks,
    "enable_party_member_hooks": handle_enable_party_member_hooks,
    "suppress_recovery": handle_suppress_recovery,
    "load_party": handle_load_party,
}
