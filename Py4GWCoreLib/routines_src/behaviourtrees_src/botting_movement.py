"""
Reusable Botting movement and map state helpers.

This module is shared by JSON adapters and other routine surfaces. It depends
only on Botting-style runtime objects and plain parameters.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable, Iterable


Point2D = tuple[float, float]
LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def cutscene_active() -> bool:
    try:
        from Py4GWCoreLib import GLOBAL_CACHE, Map

        return bool(Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.IsInCinematic())
    except Exception:
        return False


def request_skip_cinematic() -> bool:
    try:
        from Py4GWCoreLib import Map

        if not cutscene_active():
            return False
        Map.SkipCinematic()
        return True
    except Exception:
        return False


def add_path_state(bot, points: Iterable[tuple[float, float]], name: str) -> None:
    path_points = [(float(x), float(y)) for x, y in points]

    def _run_path():
        for point_i, (x, y) in enumerate(path_points):
            if cutscene_active():
                return
            step_name = f"{name} [{point_i + 1}/{len(path_points)}]"
            yield from bot.Move._coro_xy(float(x), float(y), step_name=step_name)
            if cutscene_active():
                return

    bot.States.AddCustomState(_run_path, str(name))


def add_move_state(bot, x: float, y: float, name: str) -> None:
    def _move():
        if cutscene_active():
            return
        yield from bot.Move._coro_xy(float(x), float(y), step_name=name)

    bot.States.AddCustomState(_move, str(name))


def add_nudge_move_state(
    bot,
    x: float,
    y: float,
    *,
    name: str,
    pulses: int = 1,
    pulse_ms: int = 250,
) -> None:
    def _nudge():
        from Py4GWCoreLib import Player

        pulse_count = max(1, int(pulses))
        for pulse_idx in range(pulse_count):
            if cutscene_active():
                return
            Player.Move(float(x), float(y))
            if pulse_ms > 0 and pulse_idx < (pulse_count - 1):
                yield from bot.Wait._coro_for_time(max(0, int(pulse_ms)))
                if cutscene_active():
                    return

    bot.States.AddCustomState(_nudge, str(name))


def add_wait_out_of_combat_state(bot, name: str = "Wait Out Of Combat") -> None:
    def _wait_out_of_combat():
        from Py4GWCoreLib import Range, Routines

        while Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot):
            if cutscene_active():
                return
            yield from bot.Wait._coro_for_time(1000)

    bot.States.AddCustomState(_wait_out_of_combat, str(name))


def add_wait_map_load_state(bot, *, target_map_id: int = 0, name: str = "Wait Map Load") -> None:
    def _wait_map_load():
        if cutscene_active():
            return
        yield from bot.Wait._coro_for_map_load(target_map_id=int(target_map_id or 0))

    bot.States.AddCustomState(_wait_map_load, str(name))


def add_wait_map_change_state(bot, *, target_map_id: int = 0, name: str = "Wait Map Change") -> None:
    def _wait_map_change():
        if cutscene_active():
            return
        if int(target_map_id or 0) > 0:
            yield from bot.Wait._coro_for_map_to_change(target_map_id=int(target_map_id))
        else:
            yield from bot.Wait._coro_for_map_to_change()

    bot.States.AddCustomState(_wait_map_change, str(name))


def dispatch_travel(bot, *, target_map_id: int = 0, target_map_name: str = "", leave_party: bool = True) -> None:
    if leave_party:
        bot.Party.LeaveParty()
    bot.Map.Travel(target_map_id=int(target_map_id or 0), target_map_name=str(target_map_name or ""))


def _resolve_map_id(target_map_id: int, target_map_name: str) -> int:
    from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id

    resolved_map_id = int(target_map_id or 0)
    target_name = str(target_map_name or "").strip()
    if resolved_map_id <= 0 and target_name:
        resolved_map_id = int(name_to_map_id.get(target_name, 0))
    return resolved_map_id


def _default_random_travel_districts() -> list[str]:
    from Py4GWCoreLib.enums_src.Region_enums import District

    return [
        District.EuropeItalian.name,
        District.EuropeSpanish.name,
        District.EuropePolish.name,
        District.EuropeRussian.name,
    ]


def _coerce_random_travel_districts(districts: Iterable[object] | None) -> list[int]:
    from Py4GWCoreLib.enums_src.Region_enums import District

    raw_districts = list(districts) if districts is not None else _default_random_travel_districts()
    allowed_districts: list[int] = []
    for raw_district in raw_districts:
        if isinstance(raw_district, str):
            district = District.__members__.get(raw_district.strip())
            if district is not None:
                allowed_districts.append(int(district.value))
                continue
        try:
            district_value = int(raw_district)
        except Exception:
            continue
        if district_value in District._value2member_map_:
            allowed_districts.append(district_value)

    allowed_districts = [
        district for district in allowed_districts if district not in (District.Current.value, District.Unknown.value)
    ]
    return allowed_districts or [
        District.EuropeItalian.value,
        District.EuropeSpanish.value,
        District.EuropePolish.value,
        District.EuropeRussian.value,
    ]


def add_random_travel_state(
    bot,
    *,
    target_map_id: int = 0,
    target_map_name: str = "",
    districts: Iterable[object] | None = None,
    leave_party: bool = True,
    settle_wait_ms: int = 500,
    name: str = "Random Travel",
    log: LogFn | None = None,
) -> None:
    import random

    log_fn = log or _noop_log
    resolved_map_id = _resolve_map_id(target_map_id, target_map_name)
    if resolved_map_id <= 0:
        log_fn("random_travel skipped: unresolved target map.")
        return

    allowed_districts = _coerce_random_travel_districts(districts)

    def _travel() -> None:
        from Py4GWCoreLib import Map

        district = int(random.choice(allowed_districts))
        Map.TravelToDistrict(resolved_map_id, district=district)

    if leave_party:
        bot.Party.LeaveParty()
    bot.States.AddCustomState(_travel, str(name))
    if settle_wait_ms > 0:
        bot.Wait.ForTime(int(settle_wait_ms))
    bot.Wait.ForMapLoad(target_map_id=resolved_map_id)


def add_enter_challenge_state(
    bot,
    *,
    name: str = "Enter Challenge",
    delay_ms: int = 2000,
    target_map_id: int = 0,
) -> None:
    def _enter_challenge():
        from Py4GWCoreLib import Key, Keystroke, Map

        if cutscene_active():
            return
        Map.EnterChallenge()
        if delay_ms > 0:
            yield from bot.Wait._coro_for_time(int(delay_ms))
        if cutscene_active():
            return
        Keystroke.PressAndRelease(getattr(Key, "Enter").value)
        if cutscene_active():
            return
        if int(target_map_id or 0) > 0:
            yield from bot.Wait._coro_for_map_to_change(target_map_id=int(target_map_id))
        else:
            yield from bot.Wait._coro_for_map_to_change()

    bot.States.AddCustomState(_enter_challenge, str(name))


def add_exit_map_state(
    bot,
    *,
    x: float,
    y: float,
    name: str = "Exit Map",
    target_map_id: int = 0,
    target_map_name: str = "",
) -> None:
    def _exit_map_core():
        yield from bot.Move._coro_xy(float(x), float(y), step_name=str(name))
        if cutscene_active():
            return
        if int(target_map_id or 0) > 0 or target_map_name:
            yield from bot.Wait._coro_for_map_load(
                target_map_id=int(target_map_id or 0),
                target_map_name=str(target_map_name or ""),
            )

    bot.States.AddCustomState(_exit_map_core, str(name))


def add_follow_model_state(
    bot,
    *,
    model_id: int,
    follow_range: float = 600.0,
    timeout_ms: int = 0,
) -> None:
    start = monotonic()
    if timeout_ms > 0:
        bot.Move.FollowModel(
            int(model_id),
            float(follow_range),
            exit_condition=lambda _s=start, _t=int(timeout_ms): (
                cutscene_active() or (monotonic() - _s) * 1000.0 >= _t
            ),
        )
    else:
        bot.Move.FollowModel(int(model_id), float(follow_range), exit_condition=cutscene_active)
