"""
bot runtime support module

This module provides extracted runtime build/update helpers for ModularBot.
"""

from __future__ import annotations

import traceback
from time import monotonic

from Py4GWCoreLib import Console, ConsoleLog

from .runtime_native import apply_template


def is_debug_logging_enabled(self) -> bool:
    return bool(self._debug_logging)


def set_debug_logging(self, enabled: bool) -> None:
    self._debug_logging = bool(enabled)
    self._diagnostics_enabled = bool(enabled)
    try:
        setattr(self._bot.config, "modular_debug_logging", bool(enabled))
    except Exception:
        pass


def debug_log(self, message: str, message_type=Console.MessageType.Info) -> None:
    if bool(self._debug_logging):
        ConsoleLog("ModularBot", message, message_type)


def tick_cinematic_guard(self) -> None:
    try:
        from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_movement import (
            cutscene_active,
            request_skip_cinematic,
        )

        in_cinematic = cutscene_active()
        if not in_cinematic:
            setattr(self, "_cinematic_skip_queued", False)
            setattr(self, "_cinematic_seen_at", 0.0)
            return
        now = monotonic()
        seen_at = float(getattr(self, "_cinematic_seen_at", 0.0) or 0.0)
        if seen_at <= 0.0:
            setattr(self, "_cinematic_seen_at", now)
            return
        delay_ms = max(0, int(getattr(self, "_cinematic_skip_delay_ms", 3000) or 3000))
        if (now - seen_at) * 1000.0 < delay_ms:
            return
        if bool(getattr(self, "_cinematic_skip_queued", False)):
            return
        setattr(self, "_cinematic_skip_queued", True)
        if not bool(getattr(self, "_cinematic_guard_auto_skip", False)):
            self._debug_log("Cinematic detected; waiting for explicit skip_cutscene step.")
            return
        self._debug_log("Cinematic detected; queueing guard skip.")
        request_skip_cinematic()
    except Exception as exc:
        self._debug_log(f"Cinematic guard failed: {exc}", Console.MessageType.Warning)


def _configure_start_engine(self, bot) -> None:
    try:
        from Py4GWCoreLib.modular.actions import resolve_active_engine

        if self._enforce_local_native_engine:
            setattr(bot.config, "_modular_start_engine", "none")
        else:
            engine = str(resolve_active_engine() or "none").strip().lower()
            setattr(bot.config, "_modular_start_engine", "hero_ai" if engine == "hero_ai" else "none")
    except Exception:
        setattr(bot.config, "_modular_start_engine", "none")


def _configure_external_runtime(self, bot) -> None:
    return


def _register_recovery_callbacks(self, bot) -> None:
    if self._on_party_wipe is not None:
        bot.Events.OnPartyWipeCallback(
            lambda: self._handle_recovery(bot, self._on_party_wipe, "Party wipe")
        )

        def _on_party_defeated_recovery() -> None:
            if self._on_death is None and self._is_player_dead():
                self._debug_log("[Party defeated] Ignored while player is dead (on_death disabled).")
                return
            self._handle_recovery(bot, self._on_party_wipe, "Party defeated")

        bot.Events.OnPartyDefeatedCallback(_on_party_defeated_recovery)

    if self._on_death is not None:
        bot.Events.OnDeathCallback(
            lambda: self._handle_recovery(bot, self._on_death, "Player death")
        )


def _finalize_build_state(self, bot) -> None:
    self._compile_planner_impl()
    if self._phases:
        self._set_runtime_anchor(str(self._phases[0].name))

    bot.config.initialized = True
    bot.config.fsm_running = False
    bot.config.state_description = "Stopped"


def build_routine(self, bot) -> None:
    if self._planner_compiled:
        return

    self.record_diagnostics_event(
        "build_started",
        message="Building modular runtime routine.",
    )
    try:
        self._enforce_native_local_widgets()
        self._ensure_phase_headers()
        self._loop_target_phase_name = self._resolve_loop_target_phase_name()

        _configure_start_engine(self, bot)
        self._initialize_desired_auto_state_defaults()
        apply_template(bot, self._template)
        _configure_external_runtime(self, bot)
        self._apply_party_member_hooks(bot, force=True)
        _register_recovery_callbacks(self, bot)
        _finalize_build_state(self, bot)
        self.record_diagnostics_event(
            "build_succeeded",
            message=f"Runtime build complete with {len(self._phases)} phases.",
            extra={"phase_count": len(self._phases)},
        )
    except Exception as exc:
        self.record_diagnostics_event(
            "build_failed",
            message=f"{exc}",
            traceback_text=traceback.format_exc(),
        )
        self.record_diagnostics_event(
            "exception",
            message=f"Runtime build failed: {exc}",
            traceback_text=traceback.format_exc(),
        )
        raise


def _sync_ui_state_contract(self, planner_started: bool, ui_running: bool) -> None:
    if not (ui_running and (not planner_started)):
        return
    ConsoleLog(
        "ModularBot",
        "CONTRACT_VIOLATION: UI marked running while planner is stopped. Auto-correcting state.",
        Console.MessageType.Warning,
    )
    self.record_diagnostics_event(
        "CONTRACT_VIOLATION",
        message="UI running flag true while planner stopped; auto-corrected.",
    )
    self._bot.config.fsm_running = False
    self._bot.config.state_description = "Stopped"


def _handle_loop_completion(self, was_started: bool, planner_status: str) -> None:
    if not (
        self._loop
        and (not self._manual_stop_requested)
        and was_started
        and (not self._botting_tree.IsStarted())
        and planner_status == "PLANNER: Completed"
    ):
        return
    target_phase = str(self._loop_target_phase_name or "").strip()
    if target_phase:
        self._restart_from_phase(target_phase, reason="Loop")


def _finalize_update_cycle(self, was_started: bool, planner_status: str) -> None:
    self._bot.config.fsm_running = bool(self._botting_tree.IsStarted())
    self._bot.config.state_description = "Running" if self._bot.config.fsm_running else "Stopped"

    self._tick_diagnostics_runtime()
    if was_started and (not self._botting_tree.IsStarted()):
        planner_stop_toggle_summary = self._apply_desired_auto_state_defaults(reason="planner_stopped_restore")
        if isinstance(planner_stop_toggle_summary, dict):
            self._log_toggle_apply_summary(planner_stop_toggle_summary, reason="planner_stopped_restore")
        stop_reason = planner_status or "Planner stopped."
        self.record_diagnostics_event(
            "stop",
            message=f"Planner stopped: {stop_reason}",
            extra=(
                {"reason": str(stop_reason), "toggle_restore": planner_stop_toggle_summary}
                if isinstance(planner_stop_toggle_summary, dict)
                else {"reason": str(stop_reason)}
            ),
        )
        self._finalize_diagnostics(stop_reason)


def update_impl(self) -> None:
    try:
        if not self._planner_compiled:
            build_routine(self, self._bot)

        planner_started = bool(self._botting_tree.IsStarted())
        ui_running = bool(getattr(self._bot.config, "fsm_running", False))
        _sync_ui_state_contract(self, planner_started, ui_running)

        was_started = bool(self._botting_tree.IsStarted())
        if was_started:
            self._botting_tree.tick()

        planner_status = str(self._botting_tree.GetBlackboardValue("PLANNER_STATUS", "") or "")
        _handle_loop_completion(self, was_started, planner_status)
        _finalize_update_cycle(self, was_started, planner_status)
        self._bot.UI.draw_window(
            main_child_dimensions=self._main_child_dimensions,
            icon_path=self._icon_path,
            additional_ui=self._main_ui,
        )
    except Exception as exc:
        self.record_diagnostics_event(
            "exception",
            message=f"Update failed: {exc}",
            traceback_text=traceback.format_exc(),
        )
        self._bot.config.fsm_running = False
        self._bot.config.state_description = "Stopped"
        raise


def tick_bot_coroutines(self) -> None:
    if self._enforce_local_native_engine:
        self._suppress_keep_hero_ai_coroutine()
    if self._start_coroutines_once:
        if self._bot_coroutines_started:
            if self._enforce_local_native_engine:
                self._suppress_keep_hero_ai_coroutine()
            return
        try:
            self._bot._start_coroutines()
            if self._enforce_local_native_engine:
                self._suppress_keep_hero_ai_coroutine()
            self._bot_coroutines_started = True
        except Exception:
            return
        return

    try:
        self._bot._start_coroutines()
        if self._enforce_local_native_engine:
            self._suppress_keep_hero_ai_coroutine()
    except Exception:
        return


def tick_background_coroutines(self) -> None:
    for name, factory in self._background.items():
        if name in self._background_generators:
            continue
        try:
            routine = factory() if callable(factory) else factory
            if routine is not None and hasattr(routine, "__next__"):
                self._background_generators[name] = routine
        except Exception as exc:
            ConsoleLog("ModularBot", f"Failed to start background coroutine {name!r}: {exc}", Console.MessageType.Warning)

    for name, routine in list(self._background_generators.items()):
        try:
            next(routine)
        except StopIteration:
            self._background_generators.pop(name, None)
        except Exception as exc:
            self._background_generators.pop(name, None)
            ConsoleLog("ModularBot", f"Background coroutine {name!r} failed: {exc}", Console.MessageType.Warning)
