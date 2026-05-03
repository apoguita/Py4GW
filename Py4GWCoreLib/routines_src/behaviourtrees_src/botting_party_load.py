"""
Reusable party-loading helpers for Botting-style runtimes.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable


LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def add_load_party_state(
    bot,
    *,
    step: dict,
    clear_existing: bool,
    raw_hero_team: str,
    team_mode: str,
    use_priority: bool,
    fill_with_henchmen: bool,
    apply_hero_templates: bool,
    minionless: bool,
    requested_team_key: str,
    requested_max_heroes: int,
    wait_timeout_ms: int,
    wait_poll_ms: int,
    add_delay_ms: int,
    name: str = "Load Party",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import Map, Party, Routines
    from Py4GWCoreLib.modular.hero_setup_model import (
        get_hero_priority,
        get_team_by_priority,
        get_team_for_size,
        load_hero_templates,
        max_party_size_for_team_key,
        normalize_team_key,
        resolve_hero_ids,
        team_key_for_party_size,
    )

    log_fn = log or _noop_log
    expected_holder = {
        "count": 0,
        "team": requested_team_key,
        "wait_for_npc_count": bool(fill_with_henchmen or team_mode == "henchman"),
    }

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

    def _load_party():
        use_priority_team = raw_hero_team.lower() == "priority"
        runtime_team_key = normalize_team_key(requested_team_key, minionless=minionless)
        runtime_max_heroes = int(requested_max_heroes)
        required_hero_ids = resolve_hero_ids(step.get("required_hero"))
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
            for hero_id in get_hero_priority() or []:
                resolved_id = int(hero_id or 0)
                if resolved_id > 0 and resolved_id not in hero_ids:
                    hero_ids.append(resolved_id)
        else:
            hero_ids = list(get_team_for_size(runtime_max_heroes, runtime_team_key, minionless=minionless) or [])

        if (team_mode != "henchman") and (not fill_with_henchmen) and not hero_ids and not required_hero_ids:
            log_fn(
                "load_party skipped: no heroes resolved "
                f"(team={runtime_team_key!r}, max_heroes={runtime_max_heroes}, minionless={minionless})"
            )
            expected_holder["count"] = 0
            expected_holder["team"] = runtime_team_key
            return

        hero_slot_cap = max(0, map_party_size - 1) if map_party_size > 0 else len(hero_ids)
        requested_slot_cap = max(0, int(runtime_max_heroes) - 1) if runtime_max_heroes > 0 else len(hero_ids)
        if requested_slot_cap > 0:
            hero_slot_cap = min(hero_slot_cap, requested_slot_cap) if hero_slot_cap > 0 else requested_slot_cap
        if (not use_priority) and hero_slot_cap > 0 and len(hero_ids) > hero_slot_cap:
            log_fn(f"load_party trimming heroes for map party size {map_party_size}: {len(hero_ids)} -> {hero_slot_cap}")
            hero_ids = hero_ids[:hero_slot_cap]

        missing_required_ids = [hero_id for hero_id in required_hero_ids if hero_id not in hero_ids]
        if (not use_priority) and missing_required_ids:
            replace_count = len(missing_required_ids)
            hero_ids = list(missing_required_ids) if replace_count >= len(hero_ids) else hero_ids[:-replace_count] + missing_required_ids
            if hero_slot_cap > 0 and len(hero_ids) > hero_slot_cap:
                hero_ids = hero_ids[-hero_slot_cap:]
            log_fn(
                "load_party applied required heroes "
                f"(required={required_hero_ids}, missing={missing_required_ids}, team={runtime_team_key!r})"
            )

        expected_holder["count"] = int(min(len(hero_ids), hero_slot_cap if hero_slot_cap > 0 else len(hero_ids)))
        expected_holder["team"] = runtime_team_key
        if not Party.IsPartyLeader():
            log_fn("load_party skipped: not party leader.")
            return
        if not Map.IsOutpost():
            log_fn("load_party skipped: can only add heroes in outpost.")
            return
        if clear_existing:
            Party.Heroes.KickAllHeroes()
            if add_delay_ms > 0:
                yield from Routines.Yield.wait(add_delay_ms)

        existing_hero_ids: set[int] = set()
        for hero in Party.GetHeroes() or []:
            hero_id = _hero_id_from_member(hero)
            if hero_id > 0:
                existing_hero_ids.add(hero_id)

        target_count = int(hero_slot_cap if hero_slot_cap > 0 else len(hero_ids))
        player_count = max(1, int(Party.GetPlayerCount() or 1))
        npc_target_count = max(0, int(map_party_size) - int(player_count)) if map_party_size > 0 else int(target_count)
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
                resolved_id = int(hero_id or 0)
                if resolved_id <= 0 or resolved_id in existing_hero_ids:
                    continue
                before = int(Party.GetHeroCount() or 0)
                Party.Heroes.AddHero(resolved_id)
                if add_delay_ms > 0:
                    yield from Routines.Yield.wait(add_delay_ms)
                after = int(Party.GetHeroCount() or 0)
                if after <= before:
                    log_fn(f"load_party skipped unavailable/locked hero_id={resolved_id}.")
                    continue
                existing_hero_ids.add(resolved_id)
                if apply_hero_templates:
                    template_code = str((hero_templates or {}).get(str(resolved_id), "") or "").strip()
                    hero_index = _hero_party_index_one_based(resolved_id) if template_code else 0
                    if hero_index > 0:
                        try:
                            yield from Routines.Yield.Skills.LoadHeroSkillbar(int(hero_index), template_code, log=False)
                            log_fn(f"load_party applied template for hero_id={resolved_id} at hero_index={hero_index}.")
                        except Exception as exc:
                            log_fn(f"load_party failed applying template for hero_id={resolved_id}: {exc}")
                    elif template_code:
                        log_fn(f"load_party could not resolve hero index for template apply (hero_id={resolved_id}).")

        if fill_with_henchmen or team_mode == "henchman":
            raw_hench = step.get("henchman_ids", step.get("henchmen", []))
            hench_candidates: list[int] = []
            raw_values = raw_hench if isinstance(raw_hench, list) else [raw_hench]
            for value in raw_values:
                try:
                    hench_id = int(value)
                except Exception:
                    continue
                if hench_id > 0 and hench_id not in hench_candidates:
                    hench_candidates.append(hench_id)
            if not hench_candidates:
                hench_candidates = list(range(1, 33))
            for hench_id in hench_candidates:
                if int(_npc_count()) >= int(npc_target_count):
                    break
                before_npc = int(_npc_count())
                Party.Henchmen.AddHenchman(int(hench_id))
                if add_delay_ms > 0:
                    yield from Routines.Yield.wait(add_delay_ms)
                if int(_npc_count()) <= before_npc:
                    log_fn(f"load_party skipped unavailable henchman_id={int(hench_id)}.")

        final_count = int(Party.GetHeroCount() or 0)
        final_npc_count = int(_npc_count())
        expected_holder["count"] = int(min(npc_target_count, final_npc_count)) if fill_with_henchmen or team_mode == "henchman" else int(min(target_count, final_count))
        if required_hero_ids:
            missing_required = [hero_id for hero_id in required_hero_ids if hero_id not in existing_hero_ids]
            if missing_required:
                log_fn(f"load_party missing required heroes after add: {missing_required}.")

    bot.States.AddCustomState(_load_party, str(name))

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
            log_fn(
                "load_party timed out waiting for heroes "
                f"(expected={expected}, actual={actual}, team={expected_holder.get('team')!r}, timeout_ms={wait_timeout_ms}). Continuing."
            )

        bot.States.AddCustomState(_wait_for_party_load, f"{name}: Wait")
