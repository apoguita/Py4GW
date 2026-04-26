"""
actions_party_load module

This module provides party loading step handlers.
"""
from __future__ import annotations

from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, parse_step_int, wait_after_step


def handle_load_party(ctx: StepContext) -> None:
    from time import monotonic

    from Py4GWCoreLib import Map, Party, Routines
    from Py4GWCoreLib.modular.hero_setup_model import (
        get_hero_priority,
        get_team_for_size,
        get_team_by_priority,
        load_hero_templates,
        max_party_size_for_team_key,
        normalize_team_key,
        resolve_hero_ids,
        team_key_for_party_size,
    )

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

        use_priority_team = raw_hero_team.lower() == "priority"
        runtime_team_key = normalize_team_key(requested_team_key, minionless=minionless)
        runtime_max_heroes = int(requested_max_heroes)
        required_hero_ids = resolve_hero_ids(ctx.step.get("required_hero"))
        hero_templates = load_hero_templates() if apply_hero_templates else {}

        map_party_size = int(Map.GetMaxPartySize() or 0)
        if map_party_size <= 0:
            map_party_size = int(Party.GetPartySize() or 0)

        if not runtime_team_key:
            if runtime_max_heroes in (4, 6, 8):
                runtime_team_key = team_key_for_party_size(runtime_max_heroes, minionless=minionless)
            else:
                runtime_team_key = team_key_for_party_size(map_party_size or 6, minionless=minionless)

        if runtime_max_heroes <= 0:
            runtime_max_heroes = max_party_size_for_team_key(runtime_team_key)

        if use_priority_team:
            hero_ids = list(get_team_by_priority(runtime_max_heroes, required_hero_ids) or [])
            for hid in get_hero_priority() or []:
                ihid = int(hid or 0)
                if ihid > 0 and ihid not in hero_ids:
                    hero_ids.append(ihid)
        else:
            hero_ids = list(get_team_for_size(runtime_max_heroes, runtime_team_key, minionless=minionless) or [])
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
