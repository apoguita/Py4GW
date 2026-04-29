"""
bot recovery support module

This module provides extracted recovery and party-hook helpers for ModularBot.
"""

from __future__ import annotations

from typing import Callable, Optional, Union
import time

from Py4GWCoreLib import Botting, Console, ConsoleLog, Routines

from .runtime_native import PendingRecovery, is_hero_ai_runtime_active


def set_anchor(self, phase_or_header: str) -> bool:
    value = str(phase_or_header or "").strip()
    if not value:
        return False

    if self._phase_exists(value):
        self._set_runtime_anchor(phase_name=value, state_name="")
        return True

    value_l = value.lower()
    for phase_name in self._phase_headers:
        phase_l = phase_name.lower()
        if value_l == phase_l or value_l in phase_l or phase_l in value_l:
            self._set_runtime_anchor(phase_name=phase_name, state_name="")
            return True

    fsm = self._bot.config.FSM
    state_names = list(getattr(fsm, "get_state_names", lambda: [])() or [])
    if state_names and self._active_phase_name:
        matches: list[tuple[int, int, str]] = []
        for idx, state_name in enumerate(state_names):
            state_name_l = str(state_name).lower()
            if value_l == state_name_l:
                matches.append((0, idx, state_name))
            elif value_l in state_name_l or state_name_l in value_l:
                matches.append((1, idx, state_name))
        if matches:
            best_score = min(score for score, _idx, _name in matches)
            best_matches = [entry for entry in matches if entry[0] == best_score]
            current_idx = int(getattr(fsm, "get_current_state_index", lambda: -1)() or -1)
            if current_idx < 0:
                current_idx = len(state_names) - 1
            prior_matches = [entry for entry in best_matches if entry[1] <= current_idx]
            chosen = (
                max(prior_matches, key=lambda entry: entry[1])
                if prior_matches
                else min(best_matches, key=lambda entry: entry[1])
            )
            self._set_runtime_anchor(
                phase_name=str(self._active_phase_name),
                state_name=str(chosen[2]),
            )
            return True

    ConsoleLog("ModularBot", f"Set anchor failed: {value!r} not found.")
    return False


def set_party_member_hooks_enabled(self, enabled: bool) -> None:
    self._party_member_hooks_enabled = bool(enabled)
    apply_party_member_hooks(self, self._bot, force=True)
    self._debug_log(f"Party member safety hooks {'enabled' if self._party_member_hooks_enabled else 'disabled'}.")


def suppress_recovery_for(self, ms: int = 45000, max_events: int = 20, until_outpost: bool = False) -> None:
    duration_ms = max(0, int(ms))
    event_budget = max(0, int(max_events))
    self._suppress_recovery_until = time.monotonic() + (duration_ms / 1000.0)
    self._suppress_recovery_events_remaining = event_budget
    self._suppress_recovery_until_outpost = bool(until_outpost)


def should_defer_recovery_callback(self, reason: str) -> bool:
    reason_l = str(reason or "").strip().lower()
    if reason_l not in ("party wipe", "party defeated"):
        return False

    try:
        if not bool(Routines.Checks.Map.MapValid()):
            return True
        if not bool(Routines.Checks.Map.IsExplorable()):
            return True

        player_dead = self._is_player_dead()

        party_wiped = False
        try:
            party_wiped = bool(Routines.Checks.Party.IsPartyWiped())
        except Exception:
            party_wiped = False

        party_defeated = False
        try:
            from Py4GWCoreLib import GLOBAL_CACHE

            party_defeated = bool(GLOBAL_CACHE.Party.IsPartyDefeated())
        except Exception:
            party_defeated = False

        return not (player_dead or party_wiped or party_defeated)
    except Exception:
        return False


def resolve_recovery_target(self, target: Union[str, Callable]) -> tuple[Optional[str], str, str]:
    if self._runtime_anchor_phase and self._phase_exists(self._runtime_anchor_phase):
        return (
            str(self._runtime_anchor_phase),
            str(self._runtime_anchor_state or ""),
            f"anchor:{self._runtime_anchor_phase}",
        )

    phase_name = str(target or "").strip()
    if not phase_name:
        return None, "", "<none>"

    if self._phase_exists(phase_name):
        return phase_name, "", phase_name

    phase_name_l = phase_name.lower()
    for known in self._phase_headers:
        known_l = known.lower()
        if phase_name_l == known_l or phase_name_l in known_l or known_l in phase_name_l:
            return known, "", known
    return None, "", phase_name


def resolve_party_hook_engine(self, bot: Botting) -> str:
    if self._enforce_local_native_engine:
        return "none"
    start_engine = str(getattr(bot.config, "_modular_start_engine", "") or "").strip().lower()
    if start_engine == "hero_ai":
        return start_engine
    if is_hero_ai_runtime_active(bot):
        return "hero_ai"
    return "none"


def apply_party_member_hooks(self, bot: Botting, *, force: bool = False) -> None:
    engine_mode = resolve_party_hook_engine(self, bot)
    cfg = getattr(bot, "config", None)
    desired_auto_combat = True
    if cfg is not None and hasattr(cfg, "_modular_desired_auto_combat"):
        desired_auto_combat = bool(getattr(cfg, "_modular_desired_auto_combat"))

    should_wire = bool(
        self._party_member_hooks_enabled
        and desired_auto_combat
        and engine_mode in ("hero_ai", "none")
    )
    state_key = (
        bool(self._party_member_hooks_enabled),
        bool(desired_auto_combat),
        str(engine_mode),
        bool(should_wire),
    )
    if (not force) and self._party_hook_state == state_key:
        return
    self._party_hook_state = state_key

    if should_wire:
        def _guarded_party_hook(fn: Callable[[], None]) -> Callable[[], None]:
            def _wrapped() -> None:
                if self._recovery_active:
                    return
                fn()

            return _wrapped

        bot.Events.OnPartyMemberBehindCallback(
            _guarded_party_hook(lambda: bot.Templates.Routines.OnPartyMemberBehind())
        )
        bot.Events.OnPartyMemberInDangerCallback(
            _guarded_party_hook(lambda: bot.Templates.Routines.OnPartyMemberInDanger())
        )
        bot.Events.OnPartyMemberDeadBehindCallback(
            _guarded_party_hook(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
        )
        return

    bot.Events.OnPartyMemberBehindCallback(lambda: None)
    bot.Events.OnPartyMemberInDangerCallback(lambda: None)
    bot.Events.OnPartyMemberDeadBehindCallback(lambda: None)


def _is_suppressed_until_outpost(self, now: float, reason: str) -> bool:
    if now >= float(self._suppress_recovery_until):
        self._suppress_recovery_until = 0.0
        self._suppress_recovery_until_outpost = False

    if not self._suppress_recovery_until_outpost:
        return False

    try:
        map_valid = bool(Routines.Checks.Map.MapValid())
        is_explorable = bool(Routines.Checks.Map.IsExplorable()) if map_valid else False
        alive = not self._is_player_dead()
        if map_valid and (not is_explorable) and alive:
            self._suppress_recovery_until_outpost = False
            return False
        self._debug_log(f"[{reason}] Recovery suppressed (resign transition).")
        return True
    except Exception:
        self._debug_log(f"[{reason}] Recovery suppressed (resign transition, fallback).")
        return True


def _is_suppressed_in_window(self, now: float, reason: str) -> bool:
    if not (now < float(self._suppress_recovery_until) or self._suppress_recovery_events_remaining > 0):
        return False

    if self._suppress_recovery_events_remaining > 0:
        self._suppress_recovery_events_remaining = max(0, self._suppress_recovery_events_remaining - 1)
    self._debug_log(f"[{reason}] Recovery suppressed (transition/recovery window).")
    self.record_diagnostics_event(
        "recovery_deferred",
        message=f"[{reason}] Recovery suppressed by transition/recovery window.",
    )
    return True


def _queue_pending_recovery(self, phase_name: str, state_name: str, reason: str, target_label: str) -> None:
    self._recovery_active = True
    self._pending_recovery = PendingRecovery(
        phase_name=str(phase_name),
        state_name=str(state_name),
        reason=str(reason),
        requested_at=time.monotonic(),
    )
    self._debug_log(f"[{reason}] Recovery queued - target: {target_label}")
    self.record_diagnostics_event(
        "recovery_queued",
        phase=str(phase_name),
        message=f"[{reason}] Recovery queued - target: {target_label}",
    )


def handle_recovery(self, bot: Botting, target: Union[str, Callable], reason: str) -> None:
    now = time.monotonic()
    if _is_suppressed_until_outpost(self, now, reason):
        return
    if _is_suppressed_in_window(self, now, reason):
        return
    if should_defer_recovery_callback(self, reason):
        self._debug_log(f"[{reason}] Recovery deferred (map transition or no active wipe state).")
        self.record_diagnostics_event(
            "recovery_deferred",
            message=f"[{reason}] Recovery deferred by map/party readiness checks.",
        )
        return

    if callable(target) and not isinstance(target, str):
        target()
        return

    if self._recovery_active:
        self._debug_log(f"[{reason}] Recovery already active; ignoring duplicate trigger.")
        self.record_diagnostics_event(
            "recovery_deferred",
            message=f"[{reason}] Recovery already active; duplicate trigger ignored.",
        )
        return

    phase_name, state_name, target_label = resolve_recovery_target(self, target)
    if phase_name is None:
        ConsoleLog(
            "ModularBot",
            f"Recovery target not found (anchor={self._runtime_anchor_phase!r}, target={target!r}). "
            f"Available: {list(self._phase_headers.keys())}",
            Console.MessageType.Warning,
        )
        self.record_diagnostics_event(
            "recovery_failed",
            message=f"[{reason}] Recovery target not found: {target!r}",
        )
        return

    _queue_pending_recovery(self, str(phase_name), str(state_name), str(reason), str(target_label))

