"""
Run recipe — Outpost-to-outpost running with the D/A Shadow Form build.

Uses the existing OutpostRunner infrastructure:
- Route data from Sources/aC_Scripts/OutpostRunner/maps/
- D/A build manager (OutpostRunnerDA) for skill casting
- FSMHelpers for multi-zone path following with transition detection

Two APIs:
    # Direct function — registers states on a Botting instance
    run_route(bot, "Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars")

    # Phase factory — returns a Phase for ModularBot
    Run("Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars")
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase


# ──────────────────────────────────────────────────────────────────────────────
# Direct function — registers FSM states on a Botting instance
# ──────────────────────────────────────────────────────────────────────────────

def run_route(bot: "Botting", region: str, route: str) -> None:
    """
    Register FSM states to run an outpost route using the D/A runner build.

    This loads route data from the OutpostRunner map files, equips the
    runner build, starts skill casting as a managed coroutine, and follows
    the multi-zone path with full transition detection.

    Args:
        bot:    Botting instance to register states on.
        region: Region folder name (e.g. "Eye Of The North - Full Tour").
        route:  Route script name (e.g. "_1_Eotn_To_Gunnars").
    """
    from Sources.aC_Scripts.OutpostRunner.map_loader import load_map_data
    from Sources.aC_Scripts.OutpostRunner.Build_Manager import OutpostRunnerDA
    from Sources.aC_Scripts.OutpostRunner.FSMHelpers import OutpostRunnerFSMHelpers
    from Py4GWCoreLib import ConsoleLog

    # ── Load route data ───────────────────────────────────────────────
    data = load_map_data(region, route)
    outpost_id = data["ids"]["outpost_id"]
    outpost_path = data["outpost_path"]
    segments = data.get("segments", [])

    # ── Shared state across steps ─────────────────────────────────────
    helpers = OutpostRunnerFSMHelpers()
    build = OutpostRunnerDA()
    coroutine_name = f"RunnerSkills_{region}_{route}"

    # ── 1. Configure properties for running ──────────────────────────
    #       The runner handles its own survival (Shadow Form) and speed
    #       (Pious Haste, Dwarven Stability). No template fits this —
    #       we disable everything that would interfere.
    #       NOTE: These calls each add their own FSM states internally,
    #       so they must be called directly at build time (not wrapped
    #       in AddCustomState, which would defer them to runtime).
    bot.Properties.Disable("pause_on_danger")   # don't stop for enemies
    bot.Properties.Disable("halt_on_death")      # SF handles survival
    bot.Properties.Set("movement_timeout", value=-1)  # no timeout
    bot.Properties.Disable("auto_combat")        # no fighting
    bot.Properties.Disable("hero_ai")            # solo runner
    bot.Properties.Disable("auto_loot")          # don't stop for loot
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("imp")                # no imp

    # ── 2. Travel to outpost ──────────────────────────────────────────
    bot.Map.Travel(target_map_id=outpost_id)

    # ── 3. Load runner build ──────────────────────────────────────────
    bot.States.AddCustomState(
        lambda: build.LoadSkillBar(),
        "Load Runner Build",
    )
    bot.Wait.ForTime(1000)

    # ── 4. Exit outpost via outpost path ──────────────────────────────
    def _follow_outpost_path():
        helpers.current_map_data = data
        yield from helpers.follow_path(outpost_path)

    bot.States.AddCustomState(_follow_outpost_path, "Exit Outpost")

    # ── 5. Start skill casting (managed coroutine) ────────────────────
    bot.States.AddManagedCoroutine(
        coroutine_name,
        lambda: build.ProcessSkillCasting(helpers),
    )

    # ── 6. Follow explorable segments ─────────────────────────────────
    for seg_i, seg in enumerate(segments):
        seg_map_id = seg["map_id"]
        seg_path = seg["path"]

        if seg_path:
            # Create a closure that captures the correct segment data
            def _make_segment_fn(s_path, s_map_id, s_data):
                def _follow_segment():
                    yield from helpers.wait_for_map_load(s_map_id)
                    helpers.current_map_data = s_data
                    yield from helpers.follow_path(s_path)
                return _follow_segment

            bot.States.AddCustomState(
                _make_segment_fn(seg_path, seg_map_id, data),
                f"Segment {seg_i}: Map {seg_map_id}",
            )
        else:
            # Empty path = final destination — wait for arrival
            def _make_final_fn(s_map_id, s_data):
                def _wait_for_final():
                    helpers.current_map_data = s_data
                    yield from helpers.follow_path([])  # handles final segment detection
                return _wait_for_final

            bot.States.AddCustomState(
                _make_final_fn(seg_map_id, data),
                f"Arrive at Map {seg_map_id}",
            )

    # ── 7. Stop skill casting ─────────────────────────────────────────
    bot.States.RemoveManagedCoroutine(coroutine_name)

    ConsoleLog(
        "Recipe:Run",
        f"Registered run: {region} / {route} "
        f"({len(segments)} segments, outpost {outpost_id})",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Phase factory — returns a Phase for ModularBot
# ──────────────────────────────────────────────────────────────────────────────

def Run(
    region: str,
    route: str,
    name: Optional[str] = None,
) -> Phase:
    """
    Create a Phase that runs an outpost route with the D/A build.

    Args:
        region: Region folder name (e.g. "Eye Of The North - Full Tour").
        route:  Route script name (e.g. "_1_Eotn_To_Gunnars").
        name:   Optional display name (auto-generated if None).

    Returns:
        A Phase object ready to use in ModularBot.
    """
    display = name or f"Run: {route}"
    return Phase(display, lambda bot: run_route(bot, region, route))

