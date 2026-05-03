"""
Reusable Botting party state helpers.

This module is shared by JSON adapters and other routine surfaces. It depends
only on Botting-style runtime objects and plain parameters.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable


LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def add_drop_bundle_state(bot, name: str = "Drop Bundle") -> None:
    from Py4GWCoreLib import Key, Keystroke

    bot.States.AddCustomState(
        lambda: Keystroke.PressAndRelease(getattr(Key, "F2").value),
        f"{name}: F2",
    )
    bot.Wait.ForTime(200)
    bot.States.AddCustomState(
        lambda: Keystroke.PressAndRelease(getattr(Key, "F1").value),
        f"{name}: F1",
    )
    bot.Wait.ForTime(200)


def add_flag_heroes_state(
    bot,
    x: float,
    y: float,
    *,
    name: str = "Flag Heroes",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _flag_heroes() -> None:
        from Py4GWCoreLib import Map, Party

        if not Map.IsExplorable():
            log_fn("flag_heroes skipped: map is not explorable.")
            return
        if int(Party.GetHeroCount() or 0) <= 0:
            log_fn("flag_heroes skipped: no heroes in party.")
            return
        Party.Heroes.FlagAllHeroes(float(x), float(y))

    bot.States.AddCustomState(_flag_heroes, str(name))


def add_unflag_heroes_state(bot, name: str = "Unflag Heroes") -> None:
    def _unflag_heroes() -> None:
        from Py4GWCoreLib import Party

        Party.Heroes.UnflagAllHeroes()

    bot.States.AddCustomState(_unflag_heroes, str(name))


def add_force_hero_state(bot, behavior: int, *, name: str = "Force Hero State") -> None:
    def _set_hero_behavior_all(behavior_value: int = int(behavior)) -> None:
        from Py4GWCoreLib import Party

        for hero in Party.GetHeroes():
            hero_agent_id = getattr(hero, "agent_id", 0)
            if hero_agent_id:
                Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)

    bot.States.AddCustomState(_set_hero_behavior_all, str(name))


def _account_map_tuple(account) -> tuple[int, int, int, int]:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return (
        int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0),
        int(getattr(account, "MapRegion", 0) or getattr(map_obj, "Region", 0) or 0),
        int(getattr(account, "MapDistrict", 0) or getattr(map_obj, "District", 0) or 0),
        int(getattr(account, "MapLanguage", 0) or getattr(map_obj, "Language", 0) or 0),
    )


def _current_map_tuple() -> tuple[int, int, int, int]:
    from Py4GWCoreLib import Map

    return (
        int(Map.GetMapID() or 0),
        int(Map.GetRegion()[0] or 0),
        int(Map.GetDistrict() or 0),
        int(Map.GetLanguage()[0] or 0),
    )


def _same_map(
    actual: tuple[int, int, int, int],
    expected: tuple[int, int, int, int],
    require_same_district: bool,
) -> bool:
    if actual[0] <= 0 or actual[0] != expected[0]:
        return False
    return not bool(require_same_district) or actual[1:] == expected[1:]


def _account_emails(include_self: bool) -> list[str]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    my_email = str(Player.GetAccountEmail() or "").strip()
    emails: list[str] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        email = str(getattr(account, "AccountEmail", "") or "").strip()
        if not email or (email == my_email and not include_self):
            continue
        if email not in emails:
            emails.append(email)
    return emails


def add_wait_all_accounts_same_map_state(
    bot,
    *,
    timeout_ms: int = 60000,
    poll_ms: int = 500,
    include_self: bool = False,
    require_same_district: bool = False,
    name: str = "Wait All Accounts Same Map",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _wait_all_accounts_same_map():
        from Py4GWCoreLib import GLOBAL_CACHE

        expected = _current_map_tuple()
        recipients = _account_emails(include_self)
        deadline = monotonic() + (max(0, int(timeout_ms)) / 1000.0)
        if not recipients:
            log_fn("wait_all_accounts_same_map: no accounts to verify.")
            return
        while True:
            expected = _current_map_tuple() or expected
            missing = [
                email
                for email in recipients
                if not _same_map(
                    _account_map_tuple(GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)),
                    expected,
                    require_same_district,
                )
            ]
            if not missing:
                log_fn(f"wait_all_accounts_same_map: all {len(recipients)} account(s) arrived.")
                return
            if timeout_ms <= 0 or monotonic() >= deadline:
                log_fn("wait_all_accounts_same_map timed out; missing=" + ", ".join(missing))
                return
            yield from bot.Wait._coro_for_time(max(100, int(poll_ms)))

    bot.States.AddCustomState(_wait_all_accounts_same_map, str(name))
